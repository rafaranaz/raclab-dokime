# SDD-EARS: PLATFORM-130 PLATFORM-131 PLATFORM-132
import subprocess
from pathlib import Path, PurePosixPath

import pytest

from dokime.core.repository import CommitName, RefusalError
from dokime.platform.history import versions
from tests.sandbox.engines import require

CONTRACT = PurePosixPath(".dokime/changes/s/contract.yaml")


def git(project: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(project), "-c", "user.name=t", "-c", "user.email=t@example.com", *args],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()


def commit(project: Path, files: dict[str, str | None]) -> CommitName:
    for name, text in files.items():
        target = project / name
        if text is None:
            target.unlink()
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)
    git(project, "add", "--all")
    git(project, "commit", "--quiet", "--allow-empty", "--message", "change")
    return CommitName(git(project, "rev-parse", "HEAD"))


@pytest.fixture
def project(tmp_path: Path) -> Path:
    require("git")
    root = tmp_path / "project"
    root.mkdir()
    git(root, "init", "--quiet", "--initial-branch=main")
    return root


def test_each_version_of_the_path_comes_newest_first(project: Path) -> None:
    first = commit(project, {str(CONTRACT): "one\n"})
    commit(project, {"src/other.py": "x\n"})
    second = commit(project, {str(CONTRACT): "two\n"})
    assert versions(project, second, CONTRACT) == ((second, b"two\n"), (first, b"one\n"))


def test_a_commit_that_deletes_the_path_gives_no_version(project: Path) -> None:
    first = commit(project, {str(CONTRACT): "one\n"})
    gone = commit(project, {str(CONTRACT): None})
    again = commit(project, {str(CONTRACT): "three\n"})
    assert versions(project, again, CONTRACT) == ((again, b"three\n"), (first, b"one\n"))
    assert versions(project, gone, CONTRACT) == ((first, b"one\n"),)


def test_only_the_history_that_the_commit_reaches_is_read(project: Path) -> None:
    first = commit(project, {str(CONTRACT): "one\n"})
    git(project, "checkout", "--quiet", "-b", "other")
    commit(project, {str(CONTRACT): "elsewhere\n"})
    git(project, "checkout", "--quiet", "main")
    head = commit(project, {"src/other.py": "x\n"})
    assert versions(project, head, CONTRACT) == ((first, b"one\n"),)


def test_a_renamed_file_is_not_followed(project: Path) -> None:
    commit(project, {"old/contract.yaml": "renamed\n"})
    (project / CONTRACT).parent.mkdir(parents=True)
    git(project, "mv", "old/contract.yaml", str(CONTRACT))
    git(project, "-c", "user.name=t", "-c", "user.email=t@example.com", "commit", "-q", "-m", "mv")
    head = CommitName(git(project, "rev-parse", "HEAD"))
    assert versions(project, head, CONTRACT) == ((head, b"renamed\n"),)


def test_a_path_never_in_the_history_has_no_version(project: Path) -> None:
    head = commit(project, {"src/other.py": "x\n"})
    assert versions(project, head, CONTRACT) == ()


def test_the_filters_of_the_attributes_of_the_project_do_not_apply(project: Path) -> None:
    commit(project, {".gitattributes": "*.yaml filter=leak\n"})
    git(project, "config", "filter.leak.smudge", "echo LEAKED")
    head = commit(project, {str(CONTRACT): "kept\n"})
    assert versions(project, head, CONTRACT) == ((head, b"kept\n"),)


def test_an_unknown_commit_is_refused(project: Path) -> None:
    commit(project, {str(CONTRACT): "one\n"})
    with pytest.raises(RefusalError) as refused:
        versions(project, CommitName("0" * 40), CONTRACT)
    assert refused.value.finding.code == "unknown-commit"


def test_a_directory_that_is_not_a_checkout_is_refused(tmp_path: Path) -> None:
    require("git")
    with pytest.raises(RefusalError) as refused:
        versions(tmp_path, CommitName("0" * 40), CONTRACT)
    assert refused.value.finding.code == "unknown-commit"


def test_without_git_it_is_refused(project: Path) -> None:
    head = commit(project, {str(CONTRACT): "one\n"})
    with pytest.raises(RefusalError) as refused:
        versions(project, head, CONTRACT, git="no-such-git")
    assert refused.value.finding.code == "unknown-commit"


def test_a_version_on_a_merged_branch_that_was_taken_back_is_read(project: Path) -> None:
    base = commit(project, {str(CONTRACT): "v1\n"})
    git(project, "checkout", "--quiet", "-b", "side")
    leak = commit(project, {str(CONTRACT): "LEAK\n"})
    commit(project, {str(CONTRACT): "v1\n"})
    git(project, "checkout", "--quiet", "main")
    git(
        project,
        "-c",
        "user.name=t",
        "-c",
        "user.email=t@example.com",
        "merge",
        "--quiet",
        "--no-ff",
        "--no-edit",
        "side",
    )
    head = CommitName(git(project, "rev-parse", "HEAD"))
    read = versions(project, head, CONTRACT)
    assert (leak, b"LEAK\n") in read
    assert (base, b"v1\n") in read
