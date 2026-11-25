"""The command `audit`: an audit of a change over the git and the podman adapters.

It checks what it is given before it opens an adapter: the full name of the base commit, the file
of the patch, and the directory `--out`, which has to be empty and outside the project, since the
evidence never lives inside the tree it describes. The ledger of the run is kept in
`--out/ledger.jsonl` and the evidence written there as `<story>.statement.json`. SIGINT and SIGTERM
close every layer, from the inside out, as for `env check`.
"""

import argparse
import importlib.metadata
import json
import os
import re
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from pathlib import Path

from dokime.core.findings import Finding
from dokime.core.repository import CommitName, RefusalError
from dokime.core.runtime import Digest
from dokime.core.verdicts import Verdict
from dokime.evidence.run import Gate, GateNotReached, GateRan
from dokime.evidence.schema import NAME
from dokime.interfaces.audit import Audited, Ports, Request, run_audit
from dokime.interfaces.env import sigterm_raises
from dokime.interfaces.text import EXIT_CODES, summary
from dokime.platform.checkout import checkout_commit
from dokime.platform.clock import SystemClock
from dokime.platform.git import GitRepository
from dokime.platform.ledger_file import LedgerFile
from dokime.platform.randomness import seed
from dokime.platform.sealed_store import (
    AgeSealedStore,
    default_identity_path,
    load_identity,
    read_passphrase,
)
from dokime.sandbox.podman import PodmanRuntime

LEDGER = "ledger.jsonl"
"""The file of the ledger in the directory `--out`."""
DISTRIBUTION = "raclab-dokime"
"""The distribution of the harness, the name of the project in `pyproject.toml`."""
UNVERSIONED = "unversioned"
"""The version of a harness whose package is not installed."""
_FULL_NAME = re.compile(r"[0-9a-f]{40}")
_DIGEST = re.compile(r"sha256:[0-9a-f]{64}")
_VERSION = re.compile(r"[0-9A-Za-z][0-9A-Za-z.+!-]*")
HARNESS = Path(__file__).resolve().parents[1]
"""The directory of the package of the harness, whose checkout gives its commit (ADR-0068)."""


@dataclass(frozen=True)
class Harness:
    """The version of the harness, its commit, and whether the commit was asked at all."""

    version: str
    commit: CommitName | None
    asked: bool

    def said(self) -> str:
        """The commit as the text says it."""
        if not self.asked:
            return "commit not asked"
        return self.commit.text if self.commit is not None else "without a commit"


class IdentityStore:
    """The sealed store of an identity, which asks for its passphrase when it first opens."""

    def __init__(self, identity: Path, descriptor: int | None) -> None:
        self.identity, self.descriptor = identity, descriptor
        self._store: AgeSealedStore | None = None

    def seal(self, content: bytes, recipients: Sequence[str]) -> bytes:
        """An audit seals nothing."""
        raise NotImplementedError

    def open(self, sealed: bytes) -> bytes:
        """Open sealed bytes with the identity, asking for its passphrase the first time only."""
        if self._store is None:
            store, warnings = load_identity(self.identity, read_passphrase(self.descriptor))
            for warning in warnings:
                sys.stderr.write(f"dokime audit: {warning.code}: {warning.message}\n")
            self._store = store
        return self._store.open(sealed)


def relations_seed() -> int:
    """The seed of the relations of an audit, from the randomness of the system (ADR-0076)."""
    return seed()


def key_from(
    identity: Path | None, project: Path, environ: Mapping[str, str], descriptor: int | None
) -> IdentityStore | None:
    """The store of the key of the audit, or none where the key is not: the identity given, which
    has to exist outside the tree of the project, or else that of the default path when a file is
    there."""
    if identity is not None:
        path = identity.resolve()
        if path == project or path.is_relative_to(project):
            raise RefusalError(
                "inside-the-tree", f"the identity {identity} is inside the tree of the project"
            )
        if not path.is_file():
            raise RefusalError("no-identity", f"there is no identity at {identity}")
        return IdentityStore(path, descriptor)
    try:
        default = default_identity_path(environ)
    except RefusalError:
        return None
    return IdentityStore(default, descriptor) if default.is_file() else None


def audit_command(arguments: argparse.Namespace) -> int:
    """Run `audit` and return its exit code."""
    if (arguments.story is None) == (arguments.contract is None):
        sys.stderr.write("dokime audit: give exactly one of --story and --contract\n")
        raise SystemExit(2)
    out: Path = arguments.out
    as_json = arguments.format == "json"
    asked: list[CommitName | None] = []
    audited = checked_output(_audit(arguments, as_json, asked), Path(out))
    harness = Harness(_version(), asked[0] if asked else None, asked=bool(asked))
    evidence = None
    if audited.evidence is not None:
        evidence = out / audited.evidence.name
        with evidence.open("xb") as written:
            written.write(audited.evidence.data)
    if as_json:
        sys.stdout.write(json_of(audited, evidence, out / LEDGER, harness))
    else:
        sys.stdout.write(f"harness {harness.version} {harness.said()}\n")
        sys.stdout.write(text_of(audited, evidence))
    if arguments.summary is not None:
        try:
            with Path(arguments.summary).open("a", encoding="utf-8") as summary:
                summary.write(summary_of(audited, harness, arguments.story or _story_of(arguments)))
        except OSError as error:
            reason = error.strerror or type(error).__name__
            sys.stderr.write(
                f"dokime audit: the summary {arguments.summary} cannot be written: {reason}\n"
            )
            return EXIT_CODES[Verdict.ERROR]
    return EXIT_CODES[audited.verdict]


def checked_output(audited: Audited, out: Path) -> Audited:
    """The audit as it is, or ended in `ERROR` without evidence when the sentinel of the batch
    it opened is in a path, a file or a link of `out`, or in its evidence (INV-3)."""
    if audited.sentinel is None:
        return audited
    sentinel = audited.sentinel.encode()
    where = _in_output(sentinel, out)
    if where is None and audited.evidence is not None and sentinel in audited.evidence.data:
        where = "the evidence"
    if where is None:
        return audited
    message = (
        f"the sentinel of the sealed batch is in {where}: the output holds held-out content in"
        " clear, so no evidence is written; move the output directory out of the reach of an"
        " agent, or have it deleted once it has been looked at"
    )
    found = Finding(code="sentinel-in-out", message=message, verdict=Verdict.ERROR)
    return replace(
        audited, verdict=Verdict.ERROR, findings=(*audited.findings, found), evidence=None
    )


def _in_output(sentinel: bytes, out: Path) -> str | None:
    """The first path of `out` whose name, target or bytes hold the sentinel; links not followed."""
    for directory, directories, files in os.walk(out, followlinks=False):
        for name in sorted((*directories, *files)):
            path = Path(directory) / name
            relative = path.relative_to(out).as_posix()
            if sentinel in relative.encode():
                return "a path of the output"
            if path.is_symlink():
                if sentinel in os.fsencode(os.readlink(path)):
                    return f"the link {relative} of the output"
            elif path.is_file() and sentinel in path.read_bytes():
                return f"the file {relative} of the output"
    return None


def _story_of(arguments: argparse.Namespace) -> str | None:
    """The story of an audit given a contract from outside: the name of its directory."""
    return None if arguments.contract is None else Path(arguments.contract).parent.name


def _audit(arguments: argparse.Namespace, as_json: bool, asked: list[CommitName | None]) -> Audited:
    if not _FULL_NAME.fullmatch(arguments.base):
        return _ended(
            "not-a-commit-name",
            f"{arguments.base!r} is not the full name of a commit: 40 lowercase hexadecimal"
            " characters",
        )
    try:
        patch = Path(arguments.patch).read_bytes()
    except OSError as error:
        reason = error.strerror or type(error).__name__
        return _ended("unreadable-file", f"the patch {arguments.patch} cannot be read: {reason}")
    out, project = Path(arguments.out).resolve(), Path(arguments.project).resolve()
    if out == project or out.is_relative_to(project):
        return _ended(
            "out-inside-project",
            f"the directory {arguments.out} is inside the project, and the evidence never lives"
            " inside the tree it describes",
        )
    if out.exists() and (not out.is_dir() or any(out.iterdir())):
        return _ended("out-not-empty", f"the directory {arguments.out} is not an empty directory")
    try:
        key = key_from(arguments.identity, project, os.environ, arguments.passphrase_fd)
    except RefusalError as refusal:
        return Audited(verdict=Verdict.ERROR, findings=(refusal.finding,))
    try:
        with sigterm_raises(), GitRepository(arguments.project) as repository:
            asked.append(checkout_commit(HARNESS, git=str(repository.git_path)))
            out.mkdir(parents=True, exist_ok=True)
            request = Request(
                base=CommitName(arguments.base),
                patch=patch,
                harness=_version(),
                story=arguments.story,
                contract=arguments.contract,
                pack=arguments.pack,
                harness_commit=asked[0],
                relations_seed=relations_seed(),
            )
            runtime = PodmanRuntime()
            if not as_json:
                sys.stdout.write(f"program git {repository.git_path} {repository.git_version}\n")
                sys.stdout.write(f"program podman {runtime.podman_path} {runtime.podman_version}\n")
                sys.stdout.flush()
            ports = Ports(
                repository,
                runtime,
                runtime,
                Digest(runtime.observe_program_digest),
                history=repository,
                sealed=key,
            )
            return run_audit(request, ports, LedgerFile(out / LEDGER), SystemClock())
    except RefusalError as refusal:
        return Audited(verdict=Verdict.ERROR, findings=(refusal.finding,))


def summary_of(audited: Audited, harness: Harness, story: str | None) -> str:
    """The summary of the job of an audit, in Markdown, with only what dokime fixes.

    Every value is a name, a status, a verdict, a code, a version or a digest that matches its
    pattern, so the summary needs no escaping; a message or a reason, which may quote the code of
    the change, is left in the artifact.
    """
    lines = [f"## dokime audit: {audited.verdict.value}", ""]
    if story is not None and NAME.fullmatch(story):
        lines.append(f"- Story: `{story}`")
    predicate = json.loads(audited.evidence.data)["predicate"] if audited.evidence else None
    digest = predicate["contract"].get("digest") if predicate else None
    if isinstance(digest, str) and _DIGEST.fullmatch(digest):
        lines.append(f"- Contract: `{digest}`")
    if _VERSION.fullmatch(harness.version):
        commit = f"at `{harness.commit.text}`" if harness.commit else harness.said()
        lines.append(f"- Harness: `{harness.version}`, {commit}")
    if audited.evidence is not None:
        lines.append(f"- Evidence: `{audited.evidence.digest}`, in the artifact of the job")
    if audited.findings:
        codes = ", ".join(f"`{finding.code}`" for finding in audited.findings)
        lines.append(f"- Ended by: {codes}")
    if audited.gates:
        lines += ["", *_table(audited.gates)]
    return "\n".join(lines) + "\n\n"


def _table(gates: tuple[Gate, ...]) -> list[str]:
    """Each gate with its status, its verdict and the codes of its findings."""
    rows = ["| Gate | Status | Verdict | Findings |", "|---|---|---|---|"]
    for gate in gates:
        if isinstance(gate, GateRan):
            codes = ", ".join(f"`{f.code}`" for f in gate.findings) or "—"
            rows.append(f"| {gate.gate} | run | {gate.verdict.value} | {codes} |")
        else:
            status = "not-reached" if isinstance(gate, GateNotReached) else "not-applicable"
            rows.append(f"| {gate.gate} | {status} | — | — |")
    return rows


def text_of(audited: Audited, evidence: Path | None) -> str:
    """The output of `audit` as lines of text."""
    lines = [_gate_line(gate) for gate in audited.gates]
    lines.extend(_finding_line(gate, finding) for gate, finding in _findings(audited))
    if audited.evidence is not None and evidence is not None:
        lines.append(f"evidence {evidence} {audited.evidence.digest}")
    lines.append(summary(audited.verdict, [finding for _, finding in _findings(audited)]))
    return "\n".join(lines) + "\n"


def json_of(
    audited: Audited,
    evidence: Path | None,
    ledger: Path,
    harness: "Harness | None" = None,
) -> str:
    """The output of `audit` as one JSON document."""
    document: dict[str, object] = {}
    if harness is not None:
        document["harness"] = {
            "version": harness.version,
            "commit": None if harness.commit is None else harness.commit.text,
            "commit_asked": harness.asked,
        }
    document |= {
        "verdict": audited.verdict.value,
        "evidence": None
        if audited.evidence is None or evidence is None
        else {"path": str(evidence), "digest": audited.evidence.digest},
        "ledger": str(ledger),
        "gates": [_gate_document(gate) for gate in audited.gates],
        "findings": [
            {
                "gate": gate,
                "code": finding.code,
                "verdict": finding.verdict.value,
                "message": finding.message,
                "lines": list(finding.lines),
            }
            for gate, finding in _findings(audited)
        ],
    }
    return json.dumps(document, indent=2, ensure_ascii=False) + "\n"


def _findings(audited: Audited) -> list[tuple[str, Finding]]:
    of_gates = [
        (gate.gate, finding)
        for gate in audited.gates
        if isinstance(gate, GateRan)
        for finding in gate.findings
    ]
    return [*(("audit", finding) for finding in audited.findings), *of_gates]


def _gate_line(gate: Gate) -> str:
    document = _gate_document(gate)
    if document["status"] == "run":
        return f"gate {document['gate']}: run {document['verdict']}"
    return f"gate {document['gate']}: {document['status']}: {document['reason']}"


def _gate_document(gate: Gate) -> dict[str, str]:
    if isinstance(gate, GateRan):
        return {"gate": gate.gate, "status": "run", "verdict": gate.verdict.value}
    status = "not-reached" if isinstance(gate, GateNotReached) else "not-applicable"
    return {"gate": gate.gate, "status": status, "reason": gate.reason}


def _finding_line(gate: str, finding: Finding) -> str:
    lines = ""
    if finding.lines:
        word = "lines" if len(finding.lines) > 1 else "line"
        lines = f" ({word} {', '.join(str(line) for line in finding.lines)})"
    return f"{gate}: {finding.verdict.value} {finding.code}: {finding.message}{lines}"


def harness_version() -> str:
    """The version of the installed harness, or `unversioned` when it is not installed."""
    return _version()


def _version() -> str:
    try:
        return importlib.metadata.version(DISTRIBUTION)
    except importlib.metadata.PackageNotFoundError:
        return UNVERSIONED


def _ended(code: str, message: str) -> Audited:
    return Audited(
        verdict=Verdict.ERROR,
        findings=(Finding(code=code, message=message, verdict=Verdict.ERROR),),
    )
