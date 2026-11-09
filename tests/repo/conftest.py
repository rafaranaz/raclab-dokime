import shutil
import subprocess
from collections.abc import Callable
from pathlib import Path

import pytest

from tools._common import CONFIG_PATH, DEFAULT_ROOT

GitRunner = Callable[..., str]


def _run_git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, text=True, check=True
    )
    return result.stdout


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """An empty git repository with the real scopes configuration and one commit on main."""
    _run_git(tmp_path, "init", "-q", "-b", "main")
    _run_git(tmp_path, "config", "user.email", "test@example.com")
    _run_git(tmp_path, "config", "user.name", "Test")
    _run_git(tmp_path, "config", "commit.gpgsign", "false")
    (tmp_path / "tools").mkdir()
    shutil.copy(DEFAULT_ROOT / CONFIG_PATH, tmp_path / CONFIG_PATH)
    _run_git(tmp_path, "add", ".")
    _run_git(tmp_path, "commit", "-q", "-m", "chore(repo): initialize")
    return tmp_path


@pytest.fixture
def git() -> GitRunner:
    return _run_git


def write(root: Path, relative: str, content: str) -> Path:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path
