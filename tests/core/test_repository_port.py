# SDD-EARS: CORE-067 CORE-068 CORE-069 CORE-070 CORE-071 CORE-072 CORE-073
from collections.abc import Callable
from pathlib import Path
from typing import get_type_hints

import pytest

from dokime.core.findings import Finding
from dokime.core.repository import (
    Change,
    CommitName,
    HistoryCommit,
    ProjectRepository,
    RefusalError,
    RepoPath,
    TreeName,
)
from dokime.core.verdicts import Verdict

ONE = CommitName("1" * 40)
TWO = CommitName("2" * 40)
THREE = CommitName("3" * 40)


def test_the_port_offers_the_five_operations() -> None:
    public = {name for name in vars(ProjectRepository) if not name.startswith("_")}
    assert public == {
        "history",
        "change",
        "compose_with_paths",
        "compose_with_patch",
        "extract",
    }


def test_the_history_carries_commits_with_their_date_and_their_parents() -> None:
    hints = get_type_hints(ProjectRepository.history)
    assert hints["start"] is CommitName
    assert hints["return"] == tuple[HistoryCommit, ...]


def test_a_commit_of_the_history_keeps_its_date_in_whole_seconds_and_its_parents_in_order() -> None:
    commit = HistoryCommit(name=ONE, date=1767261600, parents=(THREE, TWO))
    assert (commit.name, commit.date, commit.parents) == (ONE, 1767261600, (THREE, TWO))
    assert get_type_hints(HistoryCommit)["date"] is int


def test_the_change_of_a_commit_carries_the_commit_its_one_parent_and_the_paths() -> None:
    change = Change(commit=TWO, parent=ONE, paths=(RepoPath("a.py"), RepoPath("tests/t.py")))
    assert (change.commit, change.parent, change.paths) == (
        TWO,
        ONE,
        (RepoPath("a.py"), RepoPath("tests/t.py")),
    )
    assert get_type_hints(Change)["parent"] is CommitName
    assert get_type_hints(ProjectRepository.change)["return"] is Change


def test_the_composition_with_paths_receives_a_rule_over_each_path() -> None:
    hints = get_type_hints(ProjectRepository.compose_with_paths)
    assert hints["take"] == Callable[[RepoPath], bool]


@pytest.mark.parametrize("operation", ["compose_with_paths", "compose_with_patch"])
def test_each_composition_returns_the_name_of_the_composed_tree(operation: str) -> None:
    assert get_type_hints(getattr(ProjectRepository, operation))["return"] is TreeName


def test_extraction_takes_a_tree_and_a_directory() -> None:
    hints = get_type_hints(ProjectRepository.extract)
    assert (hints["tree"], hints["directory"]) == (TreeName, Path)


def test_a_refusal_carries_a_finding_with_the_verdict_error() -> None:
    refusal = RefusalError("shallow-clone", "the repository is a shallow clone")
    assert refusal.finding == Finding(
        code="shallow-clone", message="the repository is a shallow clone", verdict=Verdict.ERROR
    )


def test_a_refusal_can_be_raised_and_caught_as_an_exception() -> None:
    with pytest.raises(RefusalError) as caught:
        raise RefusalError("not-one-parent", "the commit has two parents")
    assert caught.value.finding.code == "not-one-parent"


@pytest.mark.parametrize(
    ("code", "message", "error"),
    [
        ("Shallow_Clone", "the repository is a shallow clone", "lowercase words"),
        ("", "the repository is a shallow clone", "code"),
        ("shallow-clone", "", "message"),
    ],
)
def test_a_refusal_with_a_code_or_message_a_finding_rejects_is_rejected_with_its_error(
    code: str, message: str, error: str
) -> None:
    with pytest.raises(ValueError, match=error):
        RefusalError(code, message)
