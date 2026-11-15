# SDD-EARS: CORPUS-010 CORPUS-011 CORPUS-012 CORPUS-013 CORPUS-014
"""The self-check of each project of the corpus at its commit, with the real git and podman.

It needs the network to clone the project, to pull its base image and to install its packages, so
it runs only when `DOKIME_CORPUS=1` asks for it, which the job `corpus` of CI does (ADR-0052).
"""

import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

from tests.corpus.projects import PROJECTS, Project
from tests.sandbox.engines import ENGINES, require

ASKED = "DOKIME_CORPUS"


def asked_for() -> bool:
    return os.environ.get(ASKED) == "1"


def clone(project: Project, into: Path) -> Path:
    address = project.source["repository"]
    done = subprocess.run(
        ["git", "clone", "--quiet", address, str(into)],
        capture_output=True,
        text=True,
        check=False,
        timeout=600,
    )
    if done.returncode != 0:
        pytest.fail(f"network: cloning {address} failed: {done.stderr.strip()}")
    return into


@pytest.mark.parametrize("project", PROJECTS, ids=lambda p: p.name)
def test_the_pack_of_a_project_passes_its_self_check_at_its_commit(
    tmp_path: Path, project: Project
) -> None:
    if not asked_for():
        pytest.skip(f"the self-checks of the corpus run when {ASKED}=1 asks for them")
    require("git")
    require("podman")
    checkout = clone(project, tmp_path / "project")
    temporary = tmp_path / "temporary"
    temporary.mkdir()
    before = ENGINES["podman"].containers()
    start = time.monotonic()
    done = subprocess.run(
        [
            sys.executable,
            "-m",
            "dokime.interfaces",
            "env",
            "check",
            "--from",
            project.source["commit"],
            "--project",
            str(checkout),
            "--pack",
            str(project.pack),
        ],
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, "TMPDIR": str(temporary)},
        timeout=3600,
    )
    seconds = time.monotonic() - start
    report = f"{project.name} in {seconds:.0f} s\n{done.stdout}{done.stderr}"
    print(report)
    assert done.returncode == 0, report
    assert done.stdout.splitlines()[-1] == "PASS: no findings", report
    assert ENGINES["podman"].containers() <= before
    assert list(temporary.iterdir()) == []


def test_the_self_checks_skip_when_they_are_not_asked_for(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(ASKED, raising=False)
    assert not asked_for()
    monkeypatch.setenv(ASKED, "1")
    assert asked_for()


def test_a_clone_that_fails_is_reported_as_the_network(tmp_path: Path) -> None:
    require("git")
    project = Project("unreachable", tmp_path / "unreachable")
    project.directory.mkdir()
    (project.directory / "source.toml").write_text(
        f'repository = "{tmp_path / "no-such-repository"}"\ncommit = "{"0" * 40}"\n'
    )
    with pytest.raises(pytest.fail.Exception, match=r"^network: cloning .*no-such-repository"):
        clone(project, tmp_path / "into")
