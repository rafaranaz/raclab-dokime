# SDD-EARS: CORPUS-015
import re
import subprocess
from pathlib import Path

import pytest

from tests.corpus.clones import CLONES, clone
from tests.corpus.projects import Project


def project(root: Path) -> Project:
    directory = root / "pack" / "small"
    directory.mkdir(parents=True)
    (directory / "source.toml").write_text(
        'repository = "https://dokime.invalid/small.git"\ncommit = "' + "a" * 40 + '"\n'
    )
    return Project("small", directory)


def git(directory: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(directory), "-c", "user.name=t", "-c", "user.email=t@example.com", *args],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()


def test_a_project_is_cloned_from_the_clone_of_the_job_when_there_is_one(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    local = tmp_path / "clones" / "small"
    local.mkdir(parents=True)
    git(local, "init", "--quiet", "--initial-branch=main")
    for number in (1, 2):
        (local / "file").write_text(str(number))
        git(local, "add", "file")
        git(local, "commit", "--quiet", "--message", str(number))
    monkeypatch.setenv(CLONES, str(tmp_path / "clones"))
    cloned = clone(project(tmp_path), tmp_path / "cloned")
    assert git(cloned, "rev-list", "--count", "HEAD") == "2"
    assert git(cloned, "rev-parse", "--is-shallow-repository") == "false"
    assert git(cloned, "rev-parse", "HEAD") == git(local, "rev-parse", "HEAD")


def test_without_the_clones_of_the_job_a_project_is_cloned_from_its_address(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv(CLONES, raising=False)
    with pytest.raises(
        pytest.fail.Exception, match=re.escape("network: cloning https://dokime.invalid")
    ):
        clone(project(tmp_path), tmp_path / "cloned")
