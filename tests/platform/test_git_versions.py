# SDD-EARS: PLATFORM-133 PLATFORM-023 CORE-189
import itertools
import os
import subprocess
from pathlib import Path

import pytest

from dokime.core.repository import CommitName, FileHistory, FileVersion, RefusalError, RepoPath
from dokime.platform.git import GitRepository
from tests.sandbox.engines import require

CONTRACT = ".dokime/changes/s/contract.yaml"
PATH = RepoPath(CONTRACT)
SECONDS = itertools.count(1_700_000_000)
"""A committer date of its own for each commit, a second apart, so that the newest is one."""


def git(project: Path, *args: str) -> str:
    date = f"@{next(SECONDS)} +0000"
    return subprocess.run(
        ["git", "-C", str(project), "-c", "user.name=t", "-c", "user.email=t@example.com", *args],
        capture_output=True,
        text=True,
        check=True,
        env={**os.environ, "GIT_COMMITTER_DATE": date, "GIT_AUTHOR_DATE": date},
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


def read(project: Path, start: CommitName) -> tuple[FileVersion, ...]:
    with GitRepository(project) as repository:
        port: FileHistory = repository
        return port.versions(start, PATH)


def test_the_versions_come_newest_first_with_their_commit_and_bytes(project: Path) -> None:
    first = commit(project, {CONTRACT: "one\n"})
    commit(project, {"src/other.py": "x\n"})
    second = commit(project, {CONTRACT: "two\n"})
    assert read(project, second) == (FileVersion(second, b"two\n"), FileVersion(first, b"one\n"))


def test_a_commit_where_the_path_is_absent_gives_no_version(project: Path) -> None:
    first = commit(project, {CONTRACT: "one\n"})
    gone = commit(project, {CONTRACT: None})
    again = commit(project, {CONTRACT: "three\n"})
    assert read(project, again) == (FileVersion(again, b"three\n"), FileVersion(first, b"one\n"))
    assert read(project, gone) == (FileVersion(first, b"one\n"),)


def test_a_path_never_in_the_history_gives_no_version(project: Path) -> None:
    head = commit(project, {"src/other.py": "x\n"})
    assert read(project, head) == ()


def test_only_the_commits_reachable_from_the_start_are_read(project: Path) -> None:
    first = commit(project, {CONTRACT: "one\n"})
    git(project, "checkout", "--quiet", "-b", "other")
    commit(project, {CONTRACT: "elsewhere\n"})
    git(project, "checkout", "--quiet", "main")
    head = commit(project, {"src/other.py": "x\n"})
    assert read(project, head) == (FileVersion(first, b"one\n"),)


def test_a_rename_is_not_followed(project: Path) -> None:
    commit(project, {"old/contract.yaml": "renamed\n"})
    (project / CONTRACT).parent.mkdir(parents=True)
    git(project, "mv", "old/contract.yaml", CONTRACT)
    git(project, "commit", "--quiet", "--message", "mv")
    head = CommitName(git(project, "rev-parse", "HEAD"))
    assert read(project, head) == (FileVersion(head, b"renamed\n"),)


def test_a_version_on_a_merged_branch_is_given(project: Path) -> None:
    base = commit(project, {CONTRACT: "v1\n"})
    git(project, "checkout", "--quiet", "-b", "side")
    leak = commit(project, {CONTRACT: "LEAK\n"})
    back = commit(project, {CONTRACT: "v1\n"})
    git(project, "checkout", "--quiet", "main")
    git(project, "merge", "--quiet", "--no-ff", "--message", "merge", "side")
    merged = CommitName(git(project, "rev-parse", "HEAD"))
    found = read(project, merged)
    assert FileVersion(leak, b"LEAK\n") in found
    assert [v.commit for v in found] == [back, leak, base]


def test_an_unknown_commit_is_refused_naming_it(project: Path) -> None:
    commit(project, {CONTRACT: "one\n"})
    with pytest.raises(RefusalError) as refused:
        read(project, CommitName("0" * 40))
    assert refused.value.finding.code == "unknown-commit"
    assert "0" * 40 in refused.value.finding.message
