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
import re
import sys
from pathlib import Path

from dokime.core.findings import Finding
from dokime.core.repository import CommitName, RefusalError
from dokime.core.runtime import Digest
from dokime.core.verdicts import Verdict
from dokime.evidence.run import Gate, GateNotReached, GateRan
from dokime.interfaces.audit import Audited, Ports, Request, run_audit
from dokime.interfaces.env import sigterm_raises
from dokime.interfaces.text import EXIT_CODES, summary
from dokime.platform.clock import SystemClock
from dokime.platform.git import GitRepository
from dokime.platform.ledger_file import LedgerFile
from dokime.sandbox.podman import PodmanRuntime

LEDGER = "ledger.jsonl"
"""The file of the ledger in the directory `--out`."""
DISTRIBUTION = "raclab-dokime"
"""The distribution of the harness, the name of the project in `pyproject.toml`."""
UNVERSIONED = "unversioned"
"""The version of a harness whose package is not installed."""
_FULL_NAME = re.compile(r"[0-9a-f]{40}")


def audit_command(arguments: argparse.Namespace) -> int:
    """Run `audit` and return its exit code."""
    if (arguments.story is None) == (arguments.contract is None):
        sys.stderr.write("dokime audit: give exactly one of --story and --contract\n")
        raise SystemExit(2)
    out: Path = arguments.out
    as_json = arguments.format == "json"
    audited = _audit(arguments, as_json)
    evidence = None
    if audited.evidence is not None:
        evidence = out / audited.evidence.name
        with evidence.open("xb") as written:
            written.write(audited.evidence.data)
    if as_json:
        sys.stdout.write(json_of(audited, evidence, out / LEDGER))
    else:
        sys.stdout.write(text_of(audited, evidence))
    return EXIT_CODES[audited.verdict]


def _audit(arguments: argparse.Namespace, as_json: bool) -> Audited:
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
    out.mkdir(parents=True, exist_ok=True)
    request = Request(
        base=CommitName(arguments.base),
        patch=patch,
        harness=_version(),
        story=arguments.story,
        contract=arguments.contract,
        pack=arguments.pack,
    )
    try:
        with sigterm_raises(), GitRepository(arguments.project) as repository:
            runtime = PodmanRuntime()
            if not as_json:
                sys.stdout.write(f"program git {repository.git_path} {repository.git_version}\n")
                sys.stdout.write(f"program podman {runtime.podman_path} {runtime.podman_version}\n")
                sys.stdout.flush()
            ports = Ports(repository, runtime, runtime, Digest(runtime.observe_program_digest))
            return run_audit(request, ports, LedgerFile(out / LEDGER), SystemClock())
    except RefusalError as refusal:
        return Audited(verdict=Verdict.ERROR, findings=(refusal.finding,))


def text_of(audited: Audited, evidence: Path | None) -> str:
    """The output of `audit` as lines of text."""
    lines = [_gate_line(gate) for gate in audited.gates]
    lines.extend(_finding_line(gate, finding) for gate, finding in _findings(audited))
    if audited.evidence is not None and evidence is not None:
        lines.append(f"evidence {evidence} {audited.evidence.digest}")
    lines.append(summary(audited.verdict, [finding for _, finding in _findings(audited)]))
    return "\n".join(lines) + "\n"


def json_of(audited: Audited, evidence: Path | None, ledger: Path) -> str:
    """The output of `audit` as one JSON document."""
    document = {
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
