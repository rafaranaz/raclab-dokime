# SDD-EARS: CORPUS-030 CORPUS-031 CORPUS-032
"""A case does not change once added: its label and its expected verdict stay where they were.

The history of the repository is the record: each case is added by one commit and changed by no
other, and no file of a case is ever deleted or renamed. A correction is a new case, and the old
one is listed in `withdrawn.toml` (ADR-0055).
"""

import subprocess
from pathlib import Path

import pytest

from tests.corpus.cases import CASES, Case
from tests.corpus.projects import HERE

ROOT = HERE.parents[1]
CASES_PATHSPEC = ":(glob)tests/corpus/*/cases/**"


def git(*args: str) -> str:
    done = subprocess.run(
        ["git", "-C", str(ROOT), *args], capture_output=True, text=True, check=True
    )
    return done.stdout


def relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def test_the_history_is_whole() -> None:
    if git("rev-parse", "--is-shallow-repository").strip() != "false":
        pytest.fail("the clone is shallow, so the history cannot show that no case changed")


@pytest.mark.parametrize("case", CASES, ids=lambda case: case.key)
def test_a_case_is_added_by_one_commit_and_changed_by_no_other(case: Case) -> None:
    directory = relative(case.directory)
    commits = git("log", "--format=%H", "--", directory).split()
    assert len(commits) == 1, f"{directory} is touched by {len(commits)} commits"
    (added,) = commits
    status = git("show", "--no-renames", "--name-status", "--format=", added, "--", directory)
    kinds = {line.split("\t")[0] for line in status.splitlines() if line}
    assert kinds == {"A"}, f"{added} does not only add the files of {directory}"
    assert git("status", "--porcelain", "--", directory) == ""


def test_no_file_of_a_case_was_deleted_or_renamed() -> None:
    gone = git(
        "log", "--no-renames", "--diff-filter=D", "--name-only", "--format=", "--", CASES_PATHSPEC
    )
    assert gone.split() == [], f"files of cases were deleted or renamed: {gone.split()}"
