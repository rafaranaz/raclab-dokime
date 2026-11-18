# SDD-EARS: PLATFORM-080 PLATFORM-081 PLATFORM-082 PLATFORM-083
import os
import subprocess
from pathlib import Path

import pytest

from dokime.core.repository import CommitName
from dokime.platform.checkout import checkout_commit


def git(directory: Path, *args: str) -> str:
    environment = {
        **os.environ,
        "GIT_AUTHOR_NAME": "t",
        "GIT_AUTHOR_EMAIL": "t@example.com",
        "GIT_COMMITTER_NAME": "t",
        "GIT_COMMITTER_EMAIL": "t@example.com",
    }
    return subprocess.run(
        ["git", "-C", str(directory), *args],
        capture_output=True,
        text=True,
        check=True,
        env=environment,
    ).stdout.strip()


@pytest.fixture
def checkout(tmp_path: Path) -> Path:
    root = tmp_path / "harness"
    (root / "src" / "dokime").mkdir(parents=True)
    git(root, "init", "--quiet", "--initial-branch=main")
    (root / "src" / "dokime" / "code.py").write_text("x = 1\n")
    (root / ".gitignore").write_text("__pycache__/\n")
    git(root, "add", "--all")
    git(root, "commit", "--quiet", "--message", "one")
    return root


def test_the_commit_of_a_clean_checkout_is_that_of_its_head(checkout: Path) -> None:
    head = CommitName(git(checkout, "rev-parse", "HEAD"))
    assert checkout_commit(checkout / "src" / "dokime") == head
    assert checkout_commit(checkout) == head


def test_a_file_that_git_ignores_leaves_the_commit(checkout: Path) -> None:
    (checkout / "src" / "dokime" / "__pycache__").mkdir()
    (checkout / "src" / "dokime" / "__pycache__" / "code.pyc").write_bytes(b"x")
    assert checkout_commit(checkout) == CommitName(git(checkout, "rev-parse", "HEAD"))


def test_a_directory_outside_a_checkout_has_no_commit(tmp_path: Path) -> None:
    alone = tmp_path / "alone"
    alone.mkdir()
    assert checkout_commit(alone) is None


def test_a_checkout_without_a_commit_has_none(tmp_path: Path) -> None:
    empty = tmp_path / "empty"
    empty.mkdir()
    git(empty, "init", "--quiet")
    assert checkout_commit(empty) is None


def test_without_git_there_is_no_commit(checkout: Path) -> None:
    assert checkout_commit(checkout, git="no-such-git-for-dokime") is None


def test_a_changed_file_leaves_no_commit(checkout: Path) -> None:
    (checkout / "src" / "dokime" / "code.py").write_text("x = 2\n")
    assert checkout_commit(checkout) is None


def test_a_file_that_git_does_not_follow_leaves_no_commit(checkout: Path) -> None:
    (checkout / "src" / "dokime" / "new.py").write_text("y = 1\n")
    assert checkout_commit(checkout) is None


def test_no_program_named_by_the_configuration_runs(checkout: Path, tmp_path: Path) -> None:
    marker = tmp_path / "ran"
    program = tmp_path / "monitor.sh"
    program.write_text(f"#!/bin/sh\ntouch {marker}\n")
    program.chmod(0o755)
    git(checkout, "config", "core.fsmonitor", str(program))
    hooks = checkout / ".git" / "hooks"
    for name in ("post-index-change", "reference-transaction"):
        (hooks / name).write_text(f"#!/bin/sh\ntouch {marker}\n")
        (hooks / name).chmod(0o755)
    assert checkout_commit(checkout) == CommitName(git(checkout, "rev-parse", "HEAD"))
    assert not marker.exists()
