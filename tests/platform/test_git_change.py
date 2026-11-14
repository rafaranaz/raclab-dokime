# SDD-EARS: PLATFORM-024 PLATFORM-025 PLATFORM-026 PLATFORM-027
from pathlib import Path

import pytest

from dokime.core.repository import CommitName, RepoPath
from dokime.platform.git import GitRepository
from tests.platform.repos import Project, file, refusal


def name(text: str) -> CommitName:
    return CommitName(text)


@pytest.fixture
def project(tmp_path: Path) -> Project:
    return Project(tmp_path / "project")


def open_on(project: Project, tmp_path: Path) -> GitRepository:
    return GitRepository(project.path)


def test_the_change_gives_the_changed_the_deleted_and_the_added_paths(
    tmp_path: Path, project: Project
) -> None:
    parent = project.commit([file("kept", b"k"), file("changed", b"1"), file("gone/old.py", b"o")])
    commit = project.commit(
        [file("kept", b"k"), file("changed", b"2"), file("new/added.py", b"n")], parent
    )
    change = open_on(project, tmp_path).change(name(commit))
    assert (change.commit, change.parent) == (name(commit), name(parent))
    assert sorted(path.text for path in change.paths) == [
        "changed",
        "gone/old.py",
        "new/added.py",
    ]


def test_the_change_gives_a_path_whose_mode_alone_changed(tmp_path: Path, project: Project) -> None:
    parent = project.commit([file("run.sh", b"x")])
    commit = project.commit([file("run.sh", b"x", mode="100755")], parent)
    assert open_on(project, tmp_path).change(name(commit)).paths == (RepoPath("run.sh"),)


def test_the_change_of_a_rename_gives_the_old_and_the_new_path(
    tmp_path: Path, project: Project
) -> None:
    body = b"the same content, long enough to be found as a rename\n" * 20
    parent = project.commit([file("old/name.py", body)])
    commit = project.commit([file("new/name.py", body)], parent)
    paths = open_on(project, tmp_path).change(name(commit)).paths
    assert sorted(path.text for path in paths) == ["new/name.py", "old/name.py"]


def test_the_change_of_a_first_commit_is_refused(tmp_path: Path, project: Project) -> None:
    root = project.commit([file("a", b"0")])
    finding = refusal(lambda: open_on(project, tmp_path).change(name(root)))
    assert (finding.code, root in finding.message) == ("not-one-parent", True)


def test_the_change_of_a_merge_is_refused(tmp_path: Path, project: Project) -> None:
    root = project.commit([file("a", b"0")])
    left = project.commit([file("a", b"1")], root)
    merge = project.commit([file("a", b"1")], left, root)
    finding = refusal(lambda: open_on(project, tmp_path).change(name(merge)))
    assert (finding.code, merge in finding.message) == ("not-one-parent", True)


def test_a_changed_path_that_is_not_utf8_is_refused_quoting_its_bytes(
    tmp_path: Path, project: Project
) -> None:
    parent = project.commit([file("a", b"0")])
    commit = project.commit([file("a", b"0"), file(b"caf\xe9.py", b"latin-1")], parent)
    finding = refusal(lambda: open_on(project, tmp_path).change(name(commit)))
    assert finding.code == "path-not-utf8"
    assert repr(b"caf\xe9.py") in finding.message
