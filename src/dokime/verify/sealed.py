"""The sealed batch and the gate `sealed-examples` (ADR-0014, ADR-0072, ADR-0073).

The sealed batch is what the sealed store encrypts: the held-out examples of a contract, each with
its salt and its text as approved, the seed of the split and the canary, in canonical form
(ADR-0062). It keeps besides what the split is drawn again from, the order of the examples of the
contract before the split and the examples kept visible as already published, and each case that
holds out nothing with its reason, `single-example` or `all-published`, so that the evidence can
tell a PASS on a case without a hidden part from one with it. The canary is a copy of a held-out
example, chosen by the seed, with only its first step and, as its one expectation, a text of 32
hexadecimal digits that the caller draws at random: it cannot hold. If it holds, the comparison
accepts what it should not, the side of a false accept; an observer that makes everything fail is
not what it detects, since that gives rejections, the safe side. The canary never counts as the
failure of a requirement nor reaches the agent.

The gate checks first that the batch is the one the contract names, by the digest of the salt and
the text of each held-out example and by the split drawn again from the batch, and observes nothing
otherwise. It reads each held-out example
from its text with the requirements of the contract, observes them and the canary on the tree of
the change, and words a held-out failure as the oracle does for the agent, with no value, input or
identifier.

Whether the gate applies is decided first, from the entries `held_out` of the contract and the
sealed batch of the base, before the key: the two go together, or the gate gives an `ERROR`;
without both it does not apply, since the contract holds out no example; and without the key it
does not apply either, for its own reason.

Before it observes, the gate reads the history of the contract of the story: the base of the batch
has to be in the history of the change, the examples kept visible have to be exactly those that
`published` finds from that base, and no held-out example may be published in the history of the
change, which is `held-out-published`. A refusal of a port ends the gate in `ERROR`.
"""

import json
import random
import re
from collections import Counter
from dataclasses import dataclass, replace

from dokime.contract.check import check
from dokime.contract.held_out import held_out_digest
from dokime.contract.model import Contract, Example, Step
from dokime.core.canonical import canonical
from dokime.core.findings import Finding
from dokime.core.layout import contract_path
from dokime.core.observation import ExampleObserver, ObservationLimits
from dokime.core.repository import (
    AuditedRepository,
    CommitName,
    FileHistory,
    RefusalError,
    RepoPath,
)
from dokime.core.runtime import Digest
from dokime.core.verdicts import Verdict
from dokime.oracle.holdout import Split, feedback, split
from dokime.packs.model import Pack
from dokime.verify.examples import _observe
from dokime.verify.published import example_items, published
from dokime.verify.result import GateResult, checks_of
from dokime.verify.trees import change_tree

SEALED = "sealed-examples"
NOT_HERE = "the key is not here"
NOT_SEALED = "the contract holds out no example"
_IMPOSSIBLE = re.compile(r"[0-9a-f]{32}")
_SALT = re.compile(r"[0-9a-f]{32}")
_COMMIT = re.compile(r"[0-9a-f]{40}")


@dataclass(frozen=True)
class SealedExample:
    """A held-out example in the sealed batch: its id, its salt and its text as approved."""

    id: str
    salt: bytes
    text: str


@dataclass(frozen=True)
class Canary:
    """The canary of a batch: a copy of a held-out example whose expected value cannot hold."""

    id: str
    of: str
    expected: str


@dataclass(frozen=True)
class Unheld:
    """A case that holds out nothing, with its reason: `single-example` or `all-published`."""

    requirement: str
    case: str
    reason: str


@dataclass(frozen=True)
class Batch:
    """What the sealed store encrypts for a contract."""

    story: str
    base: str
    """The commit of the clean checkout that was sealed from, from which the audit draws again the
    examples kept visible as already published."""
    seed: int
    order: tuple[str, ...]
    kept_visible: tuple[str, ...]
    examples: tuple[SealedExample, ...]
    unheld: tuple[Unheld, ...]
    canary: Canary


REASONS = ("single-example", "all-published")


def unheld_cases(contract: Contract, done: Split) -> tuple[Unheld, ...]:
    """Each case of a split that holds out nothing, with its reason: `single-example` when it has
    one example, `all-published` when every example of a case of two or more was kept visible."""
    sizes = Counter((e.requirement, e.case) for e in contract.examples)
    return tuple(
        Unheld(
            requirement,
            case,
            "single-example" if sizes[requirement, case] == 1 else "all-published",
        )
        for requirement, case in done.cases_without_holdout
    )


def make_canary(contract: Contract, seed: int, canary_id: str, expected: str) -> Canary:
    """The canary of a contract: a held-out example chosen by the seed, with an impossible value."""
    chance = random.Random(seed)  # noqa: S311 - a draw anyone can repeat from the seed, not a secret
    return Canary(
        id=canary_id, of=chance.choice([h.id for h in contract.held_out]), expected=expected
    )


def batch_bytes(batch: Batch) -> bytes:
    """The content of a sealed batch, in canonical form."""
    return canonical(_mapping(batch)).encode()


def _mapping(batch: Batch) -> dict[str, object]:
    return {
        "format": 1,
        "story": batch.story,
        "base": batch.base,
        "seed": batch.seed,
        "order": list(batch.order),
        "kept_visible": list(batch.kept_visible),
        "examples": [{"id": e.id, "salt": e.salt.hex(), "text": e.text} for e in batch.examples],
        "without_holdout": [
            {"requirement": u.requirement, "case": u.case, "reason": u.reason} for u in batch.unheld
        ],
        "canary": {"id": batch.canary.id, "of": batch.canary.of, "expected": batch.canary.expected},
    }


def read_batch(content: bytes) -> Batch:
    """The sealed batch of a content, or a refusal."""
    try:
        data = json.loads(content)
        batch = Batch(
            story=_text(data["story"]),
            base=_commit(data["base"]),
            seed=_natural(data["seed"]),
            order=_texts(data["order"]),
            kept_visible=_texts(data["kept_visible"]),
            unheld=tuple(
                Unheld(
                    requirement=_text(u["requirement"]),
                    case=_text(u["case"]),
                    reason=_reason(u["reason"]),
                )
                for u in data["without_holdout"]
            ),
            examples=tuple(
                SealedExample(id=_text(e["id"]), salt=_salt(e["salt"]), text=_text(e["text"]))
                for e in data["examples"]
            ),
            canary=Canary(
                id=_text(data["canary"]["id"]),
                of=_text(data["canary"]["of"]),
                expected=_impossible(data["canary"]["expected"]),
            ),
        )
        fields = {"format", "story", "base", "seed", "order", "kept_visible", "examples"}
        fields.add("without_holdout")
        if data["format"] != 1 or set(data) != {*fields, "canary"}:
            raise ValueError("not the fields of a batch")
        if batch_bytes(batch) != content:
            raise ValueError("not in canonical form")
    except (ValueError, KeyError, TypeError) as error:
        raise RefusalError("unreadable-batch", "the sealed batch cannot be read") from error
    return batch


def _text(value: object) -> str:
    if not isinstance(value, str):
        raise TypeError("not a text")
    return value


def _commit(value: object) -> str:
    if not isinstance(value, str) or _COMMIT.fullmatch(value) is None:
        raise ValueError("not the full name of a commit")
    return value


def _texts(value: object) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise TypeError("not a list of texts")
    return tuple(_text(item) for item in value)


def _reason(value: object) -> str:
    if value not in REASONS:
        raise ValueError("not a reason of a case without a held-out example")
    return str(value)


def _natural(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise TypeError("not a natural integer")
    return value


def _salt(value: object) -> bytes:
    if not isinstance(value, str) or _SALT.fullmatch(value) is None:
        raise ValueError("not a salt of 16 bytes in hexadecimal")
    return bytes.fromhex(value)


def _impossible(value: object) -> str:
    if not isinstance(value, str) or _IMPOSSIBLE.fullmatch(value) is None:
        raise ValueError("not 32 hexadecimal digits")
    return value


def applicability(holds_out: bool, batched: bool, key: bool) -> GateResult | str | None:
    """Whether the gate applies, from whether the contract of the base has entries in `held_out`,
    whether the base has a sealed batch for the story, and whether the key is here: a result with a
    finding when the two of the base do not go together, which is decided before the key; the
    reason not to apply when neither is, or when the key is not here; and `None` when the gate
    runs."""
    if batched and not holds_out:
        message = "the base has a sealed batch for the story and its contract holds out no example"
        return GateResult(gate=SEALED, findings=(_mismatch(message),))
    if holds_out and not batched:
        message = "the contract holds out examples and the base has no sealed batch for the story"
        return GateResult(
            gate=SEALED,
            findings=(
                Finding(code="sealed-batch-missing", message=message, verdict=Verdict.ERROR),
            ),
        )
    if not holds_out:
        return NOT_SEALED
    return None if key else NOT_HERE


def sealed_examples(
    pack: Pack,
    contract: Contract,
    text: str,
    batch: Batch,
    base: CommitName,
    patch: bytes,
    image: Digest,
    repository: AuditedRepository,
    history: FileHistory,
    observer: ExampleObserver,
    limits: ObservationLimits,
) -> GateResult:
    """Check that the held-out examples hold on the tree of the change, and that the canary does
    not."""
    held = _held_examples(contract, batch)
    if held is None:
        message = "the sealed batch does not hold the held-out examples that the contract names"
        return GateResult(
            gate=SEALED,
            findings=(
                Finding(code="sealed-batch-mismatch", message=message, verdict=Verdict.ERROR),
            ),
        )
    try:
        told = _history(contract, text, batch, base, repository, history)
    except RefusalError as refusal:
        return GateResult(gate=SEALED, findings=(refusal.finding,))
    if told:
        return GateResult(gate=SEALED, findings=told)
    canary = _canary(held, batch.canary)
    observed = _observe(
        SEALED,
        replace(contract, examples=(*held, canary)),
        lambda: change_tree(pack, contract, base, patch, repository),
        image,
        repository,
        observer,
        limits,
        1,
    )
    if isinstance(observed, GateResult):
        return observed
    *comparisons, (canary_seen,) = observed
    lines = {h.id: h.line for h in contract.held_out}
    findings = []
    for example, (comparison,) in zip(held, comparisons, strict=True):
        if comparison.holds:
            continue
        model = example.origin == "model"
        findings.append(
            Finding(
                code="sealed-model-example-fails" if model else "sealed-example-fails",
                message=feedback(example, comparison),
                verdict=Verdict.ASK if model else Verdict.FAIL,
                lines=(lines[example.id],),
            )
        )
    if canary_seen.holds:
        message = "the canary held: the comparison accepts an expectation that cannot hold"
        findings.append(Finding(code="canary-passed", message=message, verdict=Verdict.ERROR))
    return GateResult(
        gate=SEALED,
        findings=tuple(findings),
        checks=checks_of(example.origin for example in held),
    )


def _history(
    contract: Contract,
    text: str,
    batch: Batch,
    base: CommitName,
    repository: AuditedRepository,
    history: FileHistory,
) -> tuple[Finding, ...]:
    """The findings of the history of the contract: a base of the batch out of the history of the
    change or examples kept visible other than those published from it, a mismatch; a held-out
    example published in the history of the change, `held-out-published` at its entry."""
    try:
        start = CommitName(batch.base)
    except ValueError:
        return (_mismatch("the base of the sealed batch is not the name of a commit"),)
    if start not in {commit.name for commit in repository.history(base)}:
        return (_mismatch("the base of the sealed batch is not in the history of the change"),)
    path = RepoPath(str(contract_path(contract.story)))
    sealed = [item for one in batch.examples for item in example_items("examples:\n" + one.text)]
    kept = published((*example_items(text), *sealed), history.versions(start, path))
    if tuple(name for name in batch.order if name in kept) != batch.kept_visible:
        return (
            _mismatch(
                "the examples that the sealed batch keeps visible are not those published from its"
                " base"
            ),
        )
    since = published(sealed, history.versions(base, path))
    lines = {h.id: h.line for h in contract.held_out}
    message = (
        "a held-out example is already in a version of the contract in the history, so this gate"
        " cannot answer for it: replace it with a new example and seal again"
    )
    return tuple(
        Finding(
            code="held-out-published",
            message=message,
            verdict=Verdict.ERROR,
            lines=(lines[h.id],),
        )
        for h in contract.held_out
        if h.id in since
    )


def _mismatch(message: str) -> Finding:
    return Finding(code="sealed-batch-mismatch", message=message, verdict=Verdict.ERROR)


def _held_examples(contract: Contract, batch: Batch) -> tuple[Example, ...] | None:
    """The held-out examples read from the batch, in the order of the contract, or nothing when
    the batch is not the one that the contract names."""
    sealed = {s.id: s for s in batch.examples}
    if len(sealed) != len(batch.examples) or set(sealed) != {h.id for h in contract.held_out}:
        return None
    examples = []
    for entry in contract.held_out:
        one = sealed[entry.id]
        if held_out_digest(one.salt, one.text) != entry.digest:
            return None
        read = _read(contract, one.text)
        if read is None or (read.id, read.requirement, read.case) != (
            entry.id,
            entry.requirement,
            entry.case,
        ):
            return None
        examples.append(read)
    if not _split_again(contract, batch, examples):
        return None
    return tuple(examples)


def _split_again(contract: Contract, batch: Batch, held: list[Example]) -> bool:
    """Whether the split drawn again from the seed, the examples kept visible and the order of the
    batch holds out these examples and leaves without one the cases that the batch names."""
    known = {e.id: e for e in (*contract.examples, *held)}
    if len(batch.order) != len(known) or set(batch.order) != set(known):
        return False
    before = replace(contract, examples=tuple(known[name] for name in batch.order), held_out=())
    try:
        done = split(before, batch.seed, batch.kept_visible)
    except ValueError:
        return False
    drawn = sorted(e.id for e in done.held_out)
    return drawn == sorted(e.id for e in held) and unheld_cases(before, done) == batch.unheld


def _read(contract: Contract, text: str) -> Example | None:
    """An example read from its text with the requirements of the contract."""
    requirements = "".join(
        "  - " + json.dumps({"id": r.id, "kind": r.kind, "text": r.text, "source": r.source}) + "\n"
        for r in contract.requirements
    )
    whole = (
        f"format: 1\nstory: {json.dumps(contract.story)}\nrequirements:\n{requirements}"
        f"examples:\n{text}"
    )
    checked = check(whole)
    if checked.contract is None or len(checked.contract.examples) != 1:
        return None
    return checked.contract.examples[0]


def _canary(held: tuple[Example, ...], canary: Canary) -> Example:
    """The canary as an example: the copy of a held-out example with an impossible expectation."""
    (copied,) = [example for example in held if example.id == canary.of]
    first = copied.steps[0]
    field = "stdout" if copied.boundary == "cli" else "returns"
    return replace(
        copied,
        id=canary.id,
        origin="human",
        steps=(Step(input=first.input, expect={field: canary.expected}),),
    )
