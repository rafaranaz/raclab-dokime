"""The command `env check`: the self-check of a pack over the git and the podman adapters.

`interfaces` is the composition root: it opens the adapters, names the programs they run and
hands them to `packs`, which drives the self-check. The lines of the programs are written before
the self-check starts, and the line of each candidate as soon as it has been looked at, so that a
run shows at once with what it runs and then how it goes.
"""

import argparse
import contextlib
import json
import re
import signal
import sys
import threading
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from types import FrameType

from dokime.core.findings import Finding, summarise
from dokime.core.repository import CommitName, ProjectRepository, RefusalError
from dokime.core.runtime import VerificationRuntime
from dokime.core.verdicts import Verdict
from dokime.interfaces.text import EXIT_CODES, finding_line, summary
from dokime.packs.check import check
from dokime.packs.loop import Candidate, Program, SelfCheckResult, Side, run_self_check
from dokime.platform.git import GitRepository
from dokime.sandbox.podman import PodmanRuntime

PACK = Path(".dokime") / "pack.yaml"
_FULL_NAME = re.compile(r"[0-9a-f]{40}")


@dataclass(frozen=True)
class Ports:
    """The two ports of the self-check and the programs that run them."""

    repository: ProjectRepository
    runtime: VerificationRuntime
    programs: tuple[Program, ...]


@contextlib.contextmanager
def open_ports(project: Path) -> Iterator[Ports]:
    """Open the git adapter on the project and the podman adapter, and close them afterwards."""
    with GitRepository(project) as repository:
        runtime = PodmanRuntime()
        programs = (
            Program("git", str(repository.git_path), repository.git_version),
            Program("podman", str(runtime.podman_path), runtime.podman_version),
        )
        yield Ports(repository=repository, runtime=runtime, programs=programs)


class _TerminatedError(BaseException):
    """SIGTERM reached the harness while the adapters were open."""


def _raise_terminated(_signal: int, _frame: FrameType | None) -> None:
    raise _TerminatedError


@contextlib.contextmanager
def _sigterm_raises() -> Iterator[None]:
    """Turn SIGTERM into an exception while the adapters are open, so that they close, and raise
    it again with the previous handler on the way out.

    The adapters and `packs` raise SIGTERM again with the handler they found, which is this one,
    so the layers close from the inside out and the process ends only here.
    """
    if threading.current_thread() is not threading.main_thread():
        yield
        return
    previous = signal.signal(signal.SIGTERM, _raise_terminated)
    try:
        yield
    except _TerminatedError:
        signal.signal(signal.SIGTERM, previous)
        signal.raise_signal(signal.SIGTERM)
        raise
    finally:
        signal.signal(signal.SIGTERM, previous)


def _error(code: str, message: str) -> Finding:
    return Finding(code=code, message=message, verdict=Verdict.ERROR)


def _read_pack(path: Path) -> str | Finding:
    try:
        return path.read_bytes().decode("utf-8")
    except OSError as error:
        reason = error.strerror or type(error).__name__
    except UnicodeDecodeError:
        reason = "it is not UTF-8 text"
    return _error("unreadable-file", f"the file cannot be read: {reason}")


def env_check(arguments: argparse.Namespace) -> int:
    """Run `env check` and return its exit code."""
    project: Path = arguments.project
    pack_path: Path = arguments.pack or project / PACK
    as_json = arguments.format == "json"
    result = _self_check(pack_path, project, arguments.start, as_json)
    if as_json:
        sys.stdout.write(_as_json(pack_path, result))
    else:
        lines = [finding_line(str(pack_path), finding) for finding in result.findings]
        lines.append(summary(result.verdict, result.findings))
        sys.stdout.write("\n".join(lines) + "\n")
    return EXIT_CODES[result.verdict]


def _self_check(pack_path: Path, project: Path, start: str, as_json: bool) -> SelfCheckResult:
    def ended(*findings: Finding) -> SelfCheckResult:
        return SelfCheckResult(candidates=(), findings=findings, programs=())

    if not _FULL_NAME.fullmatch(start):
        return ended(
            _error(
                "not-a-commit-name",
                f"{start!r} is not the full name of a commit: 40 lowercase hexadecimal characters",
            )
        )
    text = _read_pack(pack_path)
    if isinstance(text, Finding):
        return ended(text)
    checked = check(text)
    if checked.pack is None:
        return ended(*checked.findings)
    dockerfile = pack_path.parent / checked.pack.dockerfile
    try:
        with _sigterm_raises(), open_ports(project) as ports:
            if not as_json:
                for program in ports.programs:
                    sys.stdout.write(f"program {program.name} {program.path} {program.version}\n")
                sys.stdout.flush()
            return run_self_check(
                checked.pack,
                dockerfile,
                CommitName(start),
                ports.repository,
                ports.runtime,
                ports.programs,
                on_candidate=(lambda _: None) if as_json else _write_candidate,
            )
    except RefusalError as refusal:
        return ended(refusal.finding)


def _write_candidate(candidate: Candidate) -> None:
    sys.stdout.write(_candidate_line(candidate) + "\n")
    sys.stdout.flush()


def _candidate_line(candidate: Candidate) -> str:
    if not candidate.witness:
        return f"candidate {candidate.commit.text}: not a witness"
    return f"candidate {candidate.commit.text}: witness: {', '.join(candidate.turned_green)}"


def _side(side: Side) -> dict[str, str | None]:
    return {
        "tree": side.tree.text,
        "image": side.image.text,
        "base": side.base.platform.text if side.base else None,
    }


def _as_json(pack_path: Path, result: SelfCheckResult) -> str:
    document = {
        "pack": str(pack_path),
        "verdict": summarise(result.findings).value,
        "programs": [
            {"name": p.name, "path": p.path, "version": p.version} for p in result.programs
        ],
        "candidates": [
            {
                "commit": c.commit.text,
                "parent_side": _side(c.parent_side),
                "commit_side": _side(c.commit_side),
                "witness": c.witness,
                "turned_green": list(c.turned_green),
            }
            for c in result.candidates
        ],
        "findings": [
            {
                "code": f.code,
                "verdict": f.verdict.value,
                "message": f.message,
                "lines": list(f.lines),
            }
            for f in result.findings
        ],
    }
    return json.dumps(document, indent=2, ensure_ascii=False) + "\n"
