"""The audit of a pull request in CI, run from the checkout of its base (ADR-0071).

The workflow `audit` checks out the pull request and, apart, its base, and runs this tool from the
checkout of the base, so that neither the tool nor the harness it runs comes from the change. The
story is the description of the name of the branch (ADR-0067). A pull request that only touches
`.dokime/changes/` is a pull request of a contract: its contracts are checked, and it is not
audited, since `protected-paths` would always refuse it. A pull request whose branch gives no story,
or whose base has no contract for it, is not audited, and the summary says why. Otherwise `audit`
runs on the patch of the pull request and writes the summary of the job (ADR-0070).

The summary holds only names that match their pattern, verdicts and codes: the name of a branch and
the paths of a pull request are written by whoever opens it.
"""

import argparse
import json
import re
import subprocess
import sys
import tempfile
from collections.abc import Callable, Sequence
from pathlib import Path, PurePosixPath

type Run = Callable[[list[str], bool], subprocess.CompletedProcess[str]]

_BRANCH = re.compile(r"[a-z]+/[a-z0-9]+-(?P<story>[A-Za-z][A-Za-z0-9]*(?:-[A-Za-z0-9]+)*)")
_NAME = re.compile(r"[A-Za-z][A-Za-z0-9]*(?:-[A-Za-z0-9]+)*")
_COMMIT = re.compile(r"[0-9a-f]{40}")
_CODE = re.compile(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*")
CHANGES = ".dokime/changes/"
CONTRACT = "contract.yaml"
CODES = {"PASS": 0, "FAIL": 1, "ERROR": 2, "ASK": 3}
_RANK = {"PASS": 0, "ASK": 1, "FAIL": 2, "ERROR": 3}


def story_of(branch: str) -> str | None:
    """The story that the name of a branch gives, or none."""
    found = _BRANCH.fullmatch(branch)
    return found["story"] if found else None


def _run(command: list[str], capture: bool) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, capture_output=capture, text=True, check=False)


def _git(project: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(project), *args], capture_output=True, text=True, check=False
    )


def _dokime(*args: str) -> list[str]:
    """A command of the dokime of this checkout, with the Python this tool runs on."""
    return [sys.executable, "-m", "dokime.interfaces", *args]


def main(argv: Sequence[str] | None = None, run: Run | None = None) -> int:
    """Audit the pull request the arguments name, and return the exit code."""
    parser = argparse.ArgumentParser(description=__doc__)
    for option in ("--project", "--base", "--head", "--branch", "--out", "--summary"):
        parser.add_argument(option, required=True)
    arguments = parser.parse_args(argv)
    runner = run or _run
    project, summary = Path(arguments.project), Path(arguments.summary)
    base, head = arguments.base, arguments.head
    if not (_COMMIT.fullmatch(base) and _COMMIT.fullmatch(head)):
        _write(
            summary, "## dokime audit: not audited", "", "- The base or the head is not a commit."
        )
        return CODES["ERROR"]
    listed = _git(project, "diff", "--name-only", "-z", base, head).stdout
    paths = [path for path in listed.split("\0") if path]
    if paths and all(path.startswith(CHANGES) for path in paths):
        return _contracts(project, head, paths, summary, runner)
    story = story_of(arguments.branch)
    if story is None:
        _write(
            summary,
            "## dokime audit: not audited",
            "",
            "- The name of the branch gives no story: it is not `<type>/<scope>-<story>`.",
        )
        return CODES["PASS"]
    if _git(project, "cat-file", "-e", f"{base}:{CHANGES}{story}/{CONTRACT}").returncode != 0:
        _write(
            summary,
            "## dokime audit: not audited",
            "",
            f"- The base has no contract for the story `{story}`.",
        )
        return CODES["PASS"]
    with tempfile.TemporaryDirectory(prefix="dokime-pr-") as work:
        patch = Path(work) / "change.patch"
        patch.write_text(_git(project, "diff", "--binary", base, head).stdout)
        command = _dokime(
            "audit",
            "--project",
            str(project),
            "--base",
            base,
            "--patch",
            str(patch),
            "--story",
            story,
            "--out",
            arguments.out,
            "--summary",
            str(summary),
        )
        return runner(command, False).returncode


def _contracts(project: Path, head: str, paths: list[str], summary: Path, run: Run) -> int:
    """Check each contract that a pull request of a contract adds or changes."""
    rows: list[str] = []
    worst = "PASS"
    with tempfile.TemporaryDirectory(prefix="dokime-contracts-") as work:
        for path in sorted(paths):
            parts = PurePosixPath(path).parts
            if len(parts) != 4 or parts[3] != CONTRACT:
                continue
            shown = _git(project, "show", f"{head}:{path}")
            if shown.returncode != 0:
                continue
            story = parts[2]
            name = story if _NAME.fullmatch(story) else "a directory that is not a name"
            directory = Path(work) / str(len(rows)) / (story if _NAME.fullmatch(story) else "x")
            directory.mkdir(parents=True)
            (directory / CONTRACT).write_text(shown.stdout)
            done = run(
                _dokime("contract", "check", str(directory / CONTRACT), "--format", "json"), True
            )
            verdict, codes = _verdict_and_codes(done.stdout)
            worst = max(worst, verdict, key=_RANK.__getitem__)
            listed = ", ".join(f"`{code}`" for code in codes) or "—"
            rows.append(f"| {name} | {verdict} | {listed} |")
    lines = ["## dokime audit: contract pull request: checked, not audited", ""]
    if rows:
        lines += ["| Contract | Verdict | Findings |", "|---|---|---|", *rows]
    else:
        lines.append("- It adds or changes no contract.")
    _write(summary, *lines)
    return CODES[worst]


def _verdict_and_codes(output: str) -> tuple[str, list[str]]:
    try:
        document = json.loads(output)
        verdict = str(document["verdict"])
        codes = [str(finding["code"]) for finding in document["findings"]]
    except (ValueError, KeyError, TypeError):
        return "ERROR", []
    if verdict not in CODES:
        return "ERROR", []
    return verdict, [code for code in codes if _CODE.fullmatch(code)]


def _write(summary: Path, *lines: str) -> None:
    with summary.open("a", encoding="utf-8") as written:
        written.write("\n".join(lines) + "\n\n")


if __name__ == "__main__":
    raise SystemExit(main())
