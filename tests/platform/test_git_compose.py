# SDD-EARS: PLATFORM-027 PLATFORM-030 PLATFORM-031
from pathlib import Path

import pytest

from dokime.core.repository import CommitName, RepoPath
from dokime.platform.git import GitRepository
from tests.platform.repos import EXECUTABLE, Project, file, link, refusal


def in_tests(path: RepoPath) -> bool:
    return path.text.startswith("tests/")


@pytest.fixture
def project(tmp_path: Path) -> Project:
    return Project(tmp_path / "project")


def test_the_taken_paths_hold_exactly_the_files_of_the_source_with_their_modes(
    tmp_path: Path, project: Project
) -> None:
    base = project.commit(
        [
            file("src/code.py", b"old code\n"),
            file("tests/test_old.py", b"deleted by the source\n"),
            file("tests/test_kept.py", b"version 1\n"),
            file("tests/run.sh", b"run\n"),
        ]
    )
    expected = [
        file("src/code.py", b"old code\n"),
        file("tests/test_kept.py", b"version 2\n"),
        file("tests/test_new.py", b"added by the source\n"),
        file("tests/run.sh", b"run\n", mode=EXECUTABLE),
        link("tests/data", "../src"),
    ]
    source = project.commit(
        [
            file("src/code.py", b"new code\n"),
            file("tests/test_kept.py", b"version 2\n"),
            file("tests/test_new.py", b"added by the source\n"),
            file("tests/run.sh", b"run\n", mode=EXECUTABLE),
            link("tests/data", "../src"),
        ],
        base,
    )
    repository = GitRepository(project.path)
    tree = repository.compose_with_paths(CommitName(base), CommitName(source), in_tests)
    assert tree.text == project.tree(expected)


def test_the_paths_the_rule_does_not_take_are_kept_from_the_base(
    tmp_path: Path, project: Project
) -> None:
    base = project.commit([file("src/code.py", b"base\n"), file("README", b"base\n")])
    source = project.commit(
        [file("src/code.py", b"source\n"), file("src/more.py", b"source\n")], base
    )
    repository = GitRepository(project.path)
    tree = repository.compose_with_paths(CommitName(base), CommitName(source), in_tests)
    assert tree.text == project.tree_of(base)


def test_the_rule_is_asked_about_every_path_of_the_base_and_of_the_source(
    tmp_path: Path, project: Project
) -> None:
    base = project.commit([file("a/one", b"1"), file("both", b"b")])
    source = project.commit([file("b/two", b"2"), file("both", b"s")], base)
    asked: set[str] = set()

    def take(path: RepoPath) -> bool:
        asked.add(path.text)
        return path.text == "both"

    repository = GitRepository(project.path)
    tree = repository.compose_with_paths(CommitName(base), CommitName(source), take)
    assert asked == {"a/one", "b/two", "both"}
    assert tree.text == project.tree([file("a/one", b"1"), file("both", b"s")])


def test_a_path_of_the_base_that_is_not_utf8_is_refused_quoting_its_bytes(
    tmp_path: Path, project: Project
) -> None:
    base = project.commit([file(b"caf\xe9", b"x")])
    source = project.commit([file("tests/t.py", b"t")], base)
    repository = GitRepository(project.path)
    finding = refusal(
        lambda: repository.compose_with_paths(CommitName(base), CommitName(source), in_tests)
    )
    assert (finding.code, repr(b"caf\xe9") in finding.message) == ("path-not-utf8", True)
