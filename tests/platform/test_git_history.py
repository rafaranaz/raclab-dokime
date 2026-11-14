# SDD-EARS: PLATFORM-020 PLATFORM-021 PLATFORM-022 PLATFORM-023
from pathlib import Path

import pytest

from dokime.core.repository import CommitName, HistoryCommit
from dokime.platform.git import GitRepository
from tests.platform.repos import Project, file, refusal


def name(text: str) -> CommitName:
    return CommitName(text)


@pytest.fixture
def project(tmp_path: Path) -> Project:
    return Project(tmp_path / "project")


def open_on(project: Project, tmp_path: Path) -> GitRepository:
    return GitRepository(project.path)


def test_the_history_gives_every_reachable_commit_once(tmp_path: Path, project: Project) -> None:
    root = project.commit([file("a", b"0")], date=10)
    left = project.commit([file("a", b"1")], root, date=20)
    right = project.commit([file("b", b"2")], root, date=20)
    merge = project.commit([file("a", b"1"), file("b", b"2")], left, right, date=30)
    project.commit([file("c", b"unreachable")], date=40)
    history = open_on(project, tmp_path).history(name(merge))
    assert sorted(commit.name.text for commit in history) == sorted([root, left, right, merge])


def test_the_history_gives_the_committer_date_not_the_author_date(
    tmp_path: Path, project: Project
) -> None:
    commit = project.commit([file("a", b"0")], date=1_700_000_500, author_date=1_600_000_000)
    (only,) = open_on(project, tmp_path).history(name(commit))
    assert only == HistoryCommit(name=name(commit), date=1_700_000_500, parents=())


def test_the_history_gives_the_parents_in_the_order_the_commit_names_them(
    tmp_path: Path, project: Project
) -> None:
    root = project.commit([file("a", b"0")])
    first = project.commit([file("a", b"1")], root)
    second = project.commit([file("a", b"2")], root)
    merge = project.commit([file("a", b"3")], second, first)
    by_name = {c.name: c for c in open_on(project, tmp_path).history(name(merge))}
    assert by_name[name(merge)].parents == (name(second), name(first))
    assert by_name[name(first)].parents == (name(root),)


UNKNOWN = "0123456789abcdef" * 2 + "01234567"


def test_a_commit_that_is_not_in_the_project_is_refused_naming_it(
    tmp_path: Path, project: Project
) -> None:
    project.commit([file("a", b"0")])
    repository = open_on(project, tmp_path)
    for action in (
        lambda: repository.history(name(UNKNOWN)),
        lambda: repository.change(name(UNKNOWN)),
        lambda: repository.compose_with_paths(name(UNKNOWN), name(UNKNOWN), lambda _: True),
    ):
        finding = refusal(action)
        assert (finding.code, UNKNOWN in finding.message) == ("unknown-commit", True)


def test_a_tree_given_as_a_commit_is_refused(tmp_path: Path, project: Project) -> None:
    tree = project.tree_of(project.commit([file("a", b"0")]))
    finding = refusal(lambda: open_on(project, tmp_path).history(name(tree)))
    assert finding.code == "unknown-commit"
