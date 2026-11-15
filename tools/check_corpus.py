"""Corpus check: the JUnit report of the job corpus has one passed self-check per project.

pytest ends with 0 when the self-checks of the corpus are skipped, which they are when
`DOKIME_CORPUS` does not reach the process. The job `corpus` runs this check on their report, so
that it passes only when every project of `tests/corpus` was self-checked once and passed
(ADR-0052). It writes one line for each project, with the duration of its self-check, and says
when a failure came from the network.
"""

import argparse
import sys
from pathlib import Path
from typing import NoReturn
from xml.parsers import expat

from tools._common import DEFAULT_ROOT

CORPUS = Path("tests") / "corpus"
TEST = "tests.corpus.test_corpus_self_check"
NAME = "test_the_pack_of_a_project_passes_its_self_check_at_its_commit"
NETWORK = "network:"


class _UnreadableError(Exception):
    pass


def _refuse(*_: object) -> NoReturn:
    raise _UnreadableError("the report has a DOCTYPE")


def _cases(report: bytes) -> list[tuple[str, float, str, str]]:
    """Each self-check of the report: its project, its seconds, its outcome and its message."""
    found: list[tuple[str, float, str, str]] = []
    current: dict[str, str] = {}

    def start(tag: str, attributes: dict[str, str]) -> None:
        if tag == "testcase":
            current.clear()
            current.update(attributes, outcome="passed", message="")
        elif current and tag in ("failure", "error", "skipped"):
            current["outcome"] = "failed" if tag == "failure" else tag
            current["message"] = attributes.get("message", "")

    def end(tag: str) -> None:
        if tag != "testcase" or not current:
            return
        prefix = f"{NAME}["
        name = current.get("name", "")
        if current.get("classname") == TEST and name.startswith(prefix) and name.endswith("]"):
            project = name[len(prefix) : -1]
            seconds = float(current.get("time", "0") or 0)
            found.append((project, seconds, current["outcome"], current["message"]))
        current.clear()

    parser = expat.ParserCreate()
    parser.StartDoctypeDeclHandler = _refuse
    parser.EntityDeclHandler = _refuse
    parser.StartElementHandler = start
    parser.EndElementHandler = end
    try:
        parser.Parse(report, True)
    except expat.ExpatError as error:
        raise _UnreadableError(f"the report is not well-formed XML: {error}") from None
    return found


def check_report(report: bytes, projects: list[str]) -> tuple[bool, list[str]]:
    """Say whether every project passed once, with one line for each project."""
    cases = _cases(report)
    lines: list[str] = []
    passed = True
    for project in projects:
        runs = [case for case in cases if case[0] == project]
        if not runs:
            lines.append(f"{project}: missing from the report")
            passed = False
            continue
        if len(runs) > 1:
            lines.append(f"{project}: ran {len(runs)} times")
            passed = False
            continue
        _, seconds, outcome, message = runs[0]
        if outcome == "passed":
            lines.append(f"{project}: passed in {seconds:.0f} s")
            continue
        passed = False
        cause = (
            ": the cause was the network"
            if message.removeprefix("Failed: ").startswith(NETWORK)
            else ""
        )
        lines.append(f"{project}: {outcome}{cause} after {seconds:.0f} s")
    return passed, lines


def projects_of(root: Path) -> list[str]:
    """The projects of the corpus: the directories of `tests/corpus` with a `source.toml`."""
    return sorted(
        path.name for path in (root / CORPUS).iterdir() if (path / "source.toml").exists()
    )


def main(argv: list[str] | None = None, root: Path | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True, help="the JUnit report of the job")
    arguments = parser.parse_args(argv)
    root = root or DEFAULT_ROOT
    try:
        passed, lines = check_report(arguments.report.read_bytes(), projects_of(root))
    except (OSError, _UnreadableError) as error:
        print(f"[corpus] {arguments.report}: cannot be read: {error}")
        return 1
    for line in lines:
        print(f"[corpus] {line}")
    print("[corpus] OK" if passed else "[corpus] failed")
    sys.stdout.flush()
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
