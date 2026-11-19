# SDD-EARS: PLATFORM-134
import shutil
import stat
from pathlib import Path, PurePosixPath

import pytest

from dokime.core.repository import CommitName, RefusalError, RepoPath
from dokime.platform.git import GitRepository
from dokime.platform.history import versions
from tests.platform.test_git_versions import CONTRACT, commit, git
from tests.sandbox.engines import require


def failing_git(directory: Path, word: str) -> str:
    """A git that fails when an argument is `word`, and is the real git otherwise."""
    real = shutil.which("git")
    assert real is not None
    script = directory / "git"
    script.write_text(
        "#!/bin/sh\n"
        f'for a in "$@"; do if [ "$a" = "{word}" ]; then echo broken >&2; exit 128; fi; done\n'
        f'exec "{real}" "$@"\n'
    )
    script.chmod(script.stat().st_mode | stat.S_IXUSR)
    return str(script)


@pytest.fixture
def project(tmp_path: Path) -> tuple[Path, CommitName]:
    require("git")
    root = tmp_path / "project"
    root.mkdir()
    git(root, "init", "--quiet", "--initial-branch=main")
    commit(root, {CONTRACT: "one\n"})
    return root, commit(root, {CONTRACT: "two\n"})


def through_the_function(root: Path, head: CommitName, program: str) -> object:
    return versions(root, head, PurePosixPath(CONTRACT), git=program)


def through_the_adapter(root: Path, head: CommitName, program: str) -> object:
    with GitRepository(root, git=program) as repository:
        return repository.versions(head, RepoPath(CONTRACT))


@pytest.mark.parametrize("word", ["log", "ls-tree", "blob"])
@pytest.mark.parametrize("read", [through_the_function, through_the_adapter])
def test_a_failure_of_git_refuses_instead_of_giving_fewer_versions(
    project: tuple[Path, CommitName], tmp_path: Path, word: str, read: object
) -> None:
    root, head = project
    program = failing_git(tmp_path, word)
    assert callable(read)
    with pytest.raises(RefusalError) as refused:
        read(root, head, program)
    assert refused.value.finding.code == "git-failed"


@pytest.mark.parametrize("read", [through_the_function, through_the_adapter])
def test_the_real_git_reads_both_versions(project: tuple[Path, CommitName], read: object) -> None:
    root, head = project
    real = shutil.which("git")
    assert real is not None
    assert callable(read)
    assert len(read(root, head, real)) == 2


def test_a_commit_where_the_path_is_a_directory_gives_no_version_and_no_refusal(
    tmp_path: Path,
) -> None:
    require("git")
    root = tmp_path / "project"
    root.mkdir()
    git(root, "init", "--quiet", "--initial-branch=main")
    first = commit(root, {CONTRACT: "one\n"})
    commit(root, {CONTRACT: None})
    head = commit(root, {CONTRACT + "/inside": "a directory now\n"})
    with GitRepository(root) as repository:
        found = repository.versions(head, RepoPath(CONTRACT))
    assert [(v.commit, v.content) for v in found] == [(first, b"one\n")]
