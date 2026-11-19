"""The command `contract seal`: split an approved contract and seal its held-out examples.

It runs in the clean checkout of the project where the pull request of the contract is made. The
contract with all its examples is read from outside the tree, where the agent that works in that
checkout cannot read it, and the held-out examples are never written into the tree: the directory
of the change receives only the contract with its visible examples and its list `held_out`, and the
sealed batch. The recipients are those of `HEAD`, confirmed by a person on the terminal or through a
descriptor. Before the split, an example already in the history of the contract, by its id or by its
boundary, target and steps, is kept visible, whatever the seed, so that the held-out part of a case
is only made of examples nobody has seen. The seed, the salts and the canary come from the
randomness of the system. The ledger of the run goes to `--out`, empty and outside the project.
"""

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path

from dokime.contract.check import check
from dokime.contract.held_out import SALT_BYTES, example_texts, held_out_digest
from dokime.contract.model import Contract
from dokime.core.canonical import digest
from dokime.core.findings import Finding, summarise
from dokime.core.layout import RECIPIENTS, contract_path, sealed_path
from dokime.core.ledger import Ledger
from dokime.core.reading import read
from dokime.core.repository import CommitName, RefusalError
from dokime.core.sealed import read_recipients
from dokime.core.verdicts import Verdict
from dokime.interfaces.inputs import read_in_tree
from dokime.interfaces.text import EXIT_CODES
from dokime.oracle.holdout import split
from dokime.platform.checkout import checkout_commit
from dokime.platform.clock import SystemClock
from dokime.platform.git import GitRepository
from dokime.platform.history import versions
from dokime.platform.ledger_file import LedgerFile
from dokime.platform.randomness import random_bytes, seed
from dokime.platform.sealed_store import seal_for
from dokime.verify.sealed import Batch, SealedExample, batch_bytes, make_canary, unheld_cases
from dokime.verify.trees import base_tree

LEDGER = "ledger.jsonl"
_YES = {"y", "yes"}
_CONTENT = ("boundary", "target", "steps")


def seal_command(arguments: argparse.Namespace) -> int:
    """Seal the contract the arguments name, and return the exit code."""
    try:
        said = _seal(arguments)
    except RefusalError as refusal:
        return _ended(refusal.finding)
    sys.stdout.write(said + "\n")
    return EXIT_CODES[Verdict.PASS]


def _ended(*findings: Finding) -> int:
    for finding in findings:
        sys.stdout.write(f"{finding.verdict.value} {finding.code}: {finding.message}\n")
    verdict = summarise(findings)
    sys.stdout.write(f"{verdict.value}: not sealed\n")
    return EXIT_CODES[verdict]


def _seal(arguments: argparse.Namespace) -> str:
    project = Path(arguments.project).resolve()
    source, out = Path(arguments.contract).resolve(), Path(arguments.out).resolve()
    for path, name in ((source, "contract"), (out, "directory --out")):
        if path == project or path.is_relative_to(project):
            raise RefusalError(
                "inside-the-tree", f"the {name} {path} is inside the tree of the project"
            )
    if out.exists() and (not out.is_dir() or any(out.iterdir())):
        raise RefusalError("out-not-empty", f"the directory {out} is not an empty directory")
    head = checkout_commit(project)
    if head is None:
        raise RefusalError("not-a-clean-checkout", f"{project} is not a clean checkout of git")
    text = _read_outside(source)
    contract = _approved(text, arguments.story)
    recipients = _recipients(project, head)
    out.mkdir(parents=True, exist_ok=True)
    ledger = Ledger(LedgerFile(out / LEDGER), SystemClock())
    ledger.record("run.started", {"story": arguments.story, "base": head.text})
    ledger.record("human.asked", {"question": "recipients", "recipients": list(recipients)})
    answer = _confirmation(recipients, arguments.confirmation_fd)
    ledger.record("human.answered", {"answer": answer})
    if answer.lower() not in _YES:
        ledger.record("run.finished", {"verdict": Verdict.ERROR.value})
        raise RefusalError("recipients-not-confirmed", "the recipients were not confirmed")
    kept = _published(contract, text, project, head, arguments.story)
    drawn_seed = seed()
    done = split(contract, drawn_seed, kept)
    unheld = unheld_cases(contract, done)
    if not done.held_out:
        ledger.record("run.finished", {"verdict": Verdict.ERROR.value})
        cases = "; ".join(f"{u.requirement}/{u.case}: {u.reason}" for u in unheld)
        raise RefusalError("nothing-to-hold-out", f"no case holds out an example: {cases}")
    texts = example_texts(text)
    sealed = tuple(
        SealedExample(e.id, random_bytes(SALT_BYTES), texts[e.id]) for e in done.held_out
    )
    visible = _visible_text(text, sealed)
    written = check(visible)
    if written.contract is None or {h.id for h in written.contract.held_out} != {
        s.id for s in sealed
    }:
        raise RefusalError("split-not-written", "the contract after the split does not check")
    ids = [e.id for e in contract.examples]
    batch = Batch(
        story=contract.story,
        base=head.text,
        seed=drawn_seed,
        order=tuple(ids),
        kept_visible=tuple(name for name in ids if name in kept),
        examples=sealed,
        unheld=unheld,
        canary=make_canary(written.contract, drawn_seed, _canary_id(set(ids)), _impossible()),
    )
    content = batch_bytes(batch)
    sealed_bytes = seal_for(content, recipients)
    directory = project / str(contract_path(arguments.story)).rsplit("/", 1)[0]
    directory.mkdir(parents=True, exist_ok=True)
    (project / str(contract_path(arguments.story))).write_text(visible)
    (project / str(sealed_path(arguments.story))).write_bytes(sealed_bytes)
    ledger.record(
        "run.finished",
        {
            "verdict": Verdict.PASS.value,
            "seed": digest(drawn_seed),
            "batch": digest(content.decode()),
        },
    )
    _tell(batch)
    return f"PASS: {len(sealed)} held-out examples sealed for {len(recipients)} recipients"


def _read_outside(path: Path) -> str:
    try:
        return path.read_bytes().decode("utf-8")
    except (OSError, UnicodeDecodeError) as error:
        raise RefusalError("unreadable-file", f"the contract {path} cannot be read") from error


def _approved(text: str, story: str) -> Contract:
    checked = check(text)
    if checked.contract is None:
        stopping = [f for f in checked.findings if f.verdict in (Verdict.FAIL, Verdict.ERROR)]
        first = stopping[0]
        raise RefusalError(first.code, first.message)
    if checked.contract.story != story:
        raise RefusalError(
            "story-mismatch", f"the story of the contract is {checked.contract.story!r}"
        )
    if checked.contract.held_out:
        raise RefusalError("already-split", "the contract already holds out examples")
    return checked.contract


def _recipients(project: Path, head: CommitName) -> tuple[str, ...]:
    """The recipients of the commit of `HEAD`, never of the working tree."""
    with GitRepository(project) as repository, tempfile.TemporaryDirectory() as work:
        tree = base_tree(repository, head)
        repository.extract(tree, Path(work))
        data = read_in_tree(Path(work), RECIPIENTS)
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as error:
        raise RefusalError("unreadable-file", "the file of the recipients is not UTF-8") from error
    recipients, findings = read_recipients(text)
    if findings:
        raise RefusalError(findings[0].code, findings[0].message)
    return recipients


def _confirmation(recipients: tuple[str, ...], descriptor: int | None) -> str:
    """The answer of a person, from the descriptor given or from the terminal."""
    question = "".join(f"  {r}\n" for r in recipients)
    question = f"the batch will be sealed for these recipients of HEAD:\n{question}seal? [y/N] "
    if descriptor is not None:
        sys.stderr.write(question + "\n")
        return _line(descriptor).strip()
    try:
        terminal = os.open("/dev/tty", os.O_RDWR | os.O_NOCTTY)
    except OSError:
        raise RefusalError(
            "no-confirmation-source",
            "there is no terminal to confirm the recipients and no descriptor was given",
        ) from None
    try:
        os.write(terminal, question.encode())
        return _line(terminal).strip()
    finally:
        os.close(terminal)


def _line(descriptor: int) -> str:
    read = bytearray()
    while True:
        byte = os.read(descriptor, 1)
        if not byte or byte == b"\n":
            return read.decode("utf-8", errors="replace")
        read += byte


def _published(
    contract: Contract, text: str, project: Path, head: CommitName, story: str
) -> frozenset[str]:
    """The examples of the contract already in a version of it in the history of `HEAD`, by id or
    by their boundary, target and steps."""
    ids: set[str] = set()
    contents: set[str] = set()
    for _, data in versions(project, head, contract_path(story)):
        for item in _items(data.decode("utf-8", errors="replace")):
            if isinstance(item.get("id"), str):
                ids.add(str(item["id"]))
            contents.add(_content(item))
    mine = {
        str(item["id"]): _content(item) for item in _items(text) if isinstance(item.get("id"), str)
    }
    return frozenset(e.id for e in contract.examples if e.id in ids or mine.get(e.id) in contents)


def _items(text: str) -> list[dict[str, object]]:
    value = read(text).value
    examples = value.get("examples") if isinstance(value, dict) else None
    if not isinstance(examples, list):
        return []
    return [dict(item) for item in examples if isinstance(item, dict)]


def _content(item: dict[str, object]) -> str:
    return json.dumps({k: item.get(k) for k in _CONTENT}, sort_keys=True, default=str)


def _visible_text(text: str, sealed: tuple[SealedExample, ...]) -> str:
    """The contract without the held-out examples, and with its list `held_out`."""
    visible = text
    for one in sealed:
        visible = visible.replace(one.text, "", 1)
    if not visible.endswith("\n"):
        visible += "\n"
    entries = []
    checked = check(text).contract
    cases = {e.id: (e.requirement, e.case) for e in checked.examples} if checked else {}
    for one in sealed:
        requirement, case = cases[one.id]
        entries.append(
            f"  - id: {one.id}\n    requirement: {requirement}\n    case: {case}\n"
            f"    digest: {held_out_digest(one.salt, one.text)}\n"
        )
    return visible + "held_out:\n" + "".join(entries)


def _canary_id(taken: set[str]) -> str:
    while True:
        name = "E-" + random_bytes(2).hex()
        if name not in taken:
            return name


def _impossible() -> str:
    return random_bytes(16).hex()


def _tell(batch: Batch) -> None:
    """Name on the standard error the examples kept visible and the cases without a held-out one."""
    if batch.kept_visible:
        sys.stderr.write("kept visible, already published: " + ", ".join(batch.kept_visible) + "\n")
    for unheld in batch.unheld:
        sys.stderr.write(
            f"no held-out example in {unheld.requirement}/{unheld.case}: {unheld.reason}\n"
        )
