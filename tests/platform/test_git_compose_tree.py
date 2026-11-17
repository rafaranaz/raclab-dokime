# SDD-EARS: PLATFORM-037 PLATFORM-038 PLATFORM-039
from pathlib import Path

import pytest

from dokime.core.repository import AuditedRepository, CommitName, RepoPath, TreeName
from dokime.platform.git import GitRepository
from tests.platform.repos import EXECUTABLE, Project, file, refusal


def in_tests(path: RepoPath) -> bool:
    return path.text.startswith("tests/")


@pytest.fixture
def project(tmp_path: Path) -> Project:
    return Project(tmp_path / "project")


def files_of(repository: GitRepository, tree: TreeName, tmp_path: Path) -> dict[str, bytes]:
    out = tmp_path / "out"
    out.mkdir()
    repository.extract(tree, out)
    return {
        path.relative_to(out).as_posix(): path.read_bytes()
        for path in sorted(out.rglob("*"))
        if path.is_file()
    }


def patched(project: Project, repository: GitRepository, base: str, target: str) -> TreeName:
    patch = project.git("diff", "--binary", "--full-index", base, target)
    return repository.compose_with_patch(CommitName(base), patch)


def test_the_taken_paths_hold_exactly_the_files_of_the_commit_and_none_of_the_tree(
    project: Project, tmp_path: Path
) -> None:
    base = project.commit(
        [
            file("src/a.py", b"old\n"),
            file("tests/test_a.py", b"base\n"),
            file("tests/conftest.py", b"base\n"),
        ]
    )
    target = project.commit(
        [
            file("src/a.py", b"new\n"),
            file("tests/test_a.py", b"edited by the patch\n"),
            file("tests/conftest.py", b"edited by the patch\n"),
            file("tests/sub/conftest.py", b"added by the patch\n"),
        ],
        base,
    )
    repository = GitRepository(project.path)
    composed = repository.compose_tree_with_paths(
        patched(project, repository, base, target), CommitName(base), in_tests
    )
    assert files_of(repository, composed, tmp_path) == {
        "src/a.py": b"new\n",
        "tests/conftest.py": b"base\n",
        "tests/test_a.py": b"base\n",
    }


def test_the_modes_of_the_commit_are_kept_under_the_taken_paths(project: Project) -> None:
    base = project.commit(
        [file("src/a.py", b"a\n"), file("tests/run.sh", b"run\n", mode=EXECUTABLE)]
    )
    target = project.commit([file("src/a.py", b"b\n"), file("tests/run.sh", b"run\n")], base)
    repository = GitRepository(project.path)
    composed = repository.compose_tree_with_paths(
        patched(project, repository, base, target), CommitName(base), in_tests
    )
    expected = project.commit(
        [file("src/a.py", b"b\n"), file("tests/run.sh", b"run\n", mode=EXECUTABLE)]
    )
    assert composed == TreeName(project.tree_of(expected))


def test_the_files_of_the_tree_outside_the_taken_paths_are_kept(
    project: Project, tmp_path: Path
) -> None:
    base = project.commit([file("src/a.py", b"a\n"), file("tests/t.py", b"t\n")])
    target = project.commit(
        [file("src/a.py", b"b\n"), file("src/new.py", b"n\n"), file("tests/t.py", b"t\n")], base
    )
    repository = GitRepository(project.path)
    composed = repository.compose_tree_with_paths(
        patched(project, repository, base, target), CommitName(base), in_tests
    )
    files = files_of(repository, composed, tmp_path)
    assert (files["src/a.py"], files["src/new.py"]) == (b"b\n", b"n\n")


def test_a_tree_that_cannot_be_read_is_refused_naming_it(project: Project) -> None:
    base = project.commit([file("a", b"a\n")])
    missing = TreeName("0" * 40)
    repository = GitRepository(project.path)
    finding = refusal(
        lambda: repository.compose_tree_with_paths(missing, CommitName(base), in_tests)
    )
    assert (finding.code, missing.text in finding.message) == ("unknown-tree", True)


def test_the_adapter_is_an_audited_repository(project: Project) -> None:
    project.commit([file("a", b"a\n")])
    repository: AuditedRepository = GitRepository(project.path)
    assert callable(repository.compose_tree_with_paths)
