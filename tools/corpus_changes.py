"""Changes check: whether a part of the job corpus runs the corpus (ADR-0077).

On a pull request whose every changed file is a Markdown file under `docs/`, outside
`docs/requirements/`, the corpus does not run. The files are listed with renames turned off, so
that a file moved names both of its paths. Whenever the files cannot be listed, the pull request
changes no file, or the event is not a pull request, the corpus runs. The check writes `run=true`
or `run=false` to the outputs of the step and why to the summary of the job; the summary names a
file only when its name is plain, since the names of a pull request are written by whoever opens
it.
"""

import argparse
import re
import subprocess
from pathlib import Path

TEXT = "docs/"
NOT_TEXT = "docs/requirements/"
DID_NOT_RUN = "the corpus did not run: the pull request only changes text"
_PLAIN = re.compile(r"[A-Za-z0-9._/-]+")


class ChangesError(Exception):
    """The changed files cannot be listed."""


def runs(files: list[str]) -> bool:
    """Whether the corpus runs for a pull request that changes these files."""
    if not files:
        return True
    return not all(
        f.startswith(TEXT) and f.endswith(".md") and not f.startswith(NOT_TEXT) for f in files
    )


def changed_files(repository: Path, base: str, head: str) -> list[str]:
    """The files changed from the base to the head, with renames turned off."""
    command = [
        "git",
        "-C",
        str(repository),
        "diff",
        "--name-only",
        "--no-renames",
        base,
        head,
        "--",
    ]
    try:
        done = subprocess.run(command, capture_output=True, text=True, check=False)
    except OSError as error:
        raise ChangesError(str(error)) from None
    if done.returncode != 0 or not base:
        raise ChangesError(done.stderr.strip() or "no base was given")
    return [line for line in done.stdout.splitlines() if line]


def _named(file: str) -> str:
    return f"- `{file}`" if _PLAIN.fullmatch(file) else "- a file whose name is not plain"


def decision(event: str, repository: Path, base: str, head: str) -> tuple[bool, list[str]]:
    """Whether the corpus runs, with the lines of the summary."""
    if event != "pull_request":
        return True, [f"the corpus runs: the event is {event}, not a pull request"]
    try:
        files = changed_files(repository, base, head)
    except ChangesError as error:
        return True, [f"the corpus runs: the changed files cannot be listed: {error}"]
    if runs(files):
        reason = "it changes no file" if not files else "it changes files that are not text"
        return True, [f"the corpus runs: {reason}"]
    return False, [DID_NOT_RUN, "", *(_named(f) for f in files)]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--event", required=True, help="the name of the event of the run")
    parser.add_argument("--base", default="", help="the commit of the base of the pull request")
    parser.add_argument("--head", default="HEAD", help="the commit of the change")
    parser.add_argument("--repository", type=Path, default=Path(), help="the checkout")
    parser.add_argument("--output", type=Path, required=True, help="the outputs of the step")
    parser.add_argument("--summary", type=Path, required=True, help="the summary of the job")
    arguments = parser.parse_args(argv)
    run, lines = decision(arguments.event, arguments.repository, arguments.base, arguments.head)
    with arguments.output.open("a") as output:
        output.write(f"run={'true' if run else 'false'}\n")
    with arguments.summary.open("a") as summary:
        summary.write("\n".join(lines) + "\n")
    for line in lines:
        print(f"[corpus] {line}" if line else "")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
