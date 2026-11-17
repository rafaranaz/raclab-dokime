# SDD-EARS: INTERFACES-010 INTERFACES-012 INTERFACES-056 INTERFACES-057 INTERFACES-059
"""`env check` with the real git and podman, on a small repository made for the test.

The tests of the project are files that each name the code they expect, and `run.sh`, run in a
busybox image, writes a JUnit report that says which of them match `src/code.txt`.
"""

import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import pytest

from tests.sandbox.engines import BUSYBOX, ENGINES, require

RUN = """\
#!/bin/sh
code=$(cat src/code.txt)
{
  echo '<testsuite>'
  for test in tests/test_*.txt; do
    name=$(basename "$test")
    if [ "$(cat "$test")" = "$code" ]; then
      echo "<testcase classname=\\"tests\\" name=\\"$name\\"/>"
    else
      echo "<testcase classname=\\"tests\\" name=\\"$name\\"><failure/></testcase>"
    fi
  done
  echo '</testsuite>'
} > /dokime/out/report.xml
"""

PACK = """\
format: 1
name: small
environment:
  dockerfile: Dockerfile
tests:
  command: {command}
  report: report.xml
  paths: ["tests/**"]
  config: ["pytest.ini"]
"""


def git(project: Path, *args: str, date: int = 1_700_000_000) -> str:
    environment = {
        **os.environ,
        "GIT_AUTHOR_NAME": "t",
        "GIT_AUTHOR_EMAIL": "t@example.com",
        "GIT_COMMITTER_NAME": "t",
        "GIT_COMMITTER_EMAIL": "t@example.com",
        "GIT_AUTHOR_DATE": f"{date} +0000",
        "GIT_COMMITTER_DATE": f"{date} +0000",
    }
    done = subprocess.run(
        ["git", "-C", str(project), *args],
        capture_output=True,
        text=True,
        check=True,
        env=environment,
    )
    return done.stdout.strip()


def commit(project: Path, files: dict[str, str], date: int) -> str:
    for path, text in files.items():
        (project / path).parent.mkdir(parents=True, exist_ok=True)
        (project / path).write_text(text)
    git(project, "add", "--all", "--", ".", ":!.dokime")
    git(project, "commit", "--quiet", "--message", str(date), date=1_700_000_000 + date)
    return git(project, "rev-parse", "HEAD")


def write_pack(directory: Path, command: str) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "pack.yaml").write_text(PACK.format(command=command))
    (directory / "Dockerfile").write_text(f"FROM {BUSYBOX}\n")
    return directory / "pack.yaml"


@pytest.fixture
def project(tmp_path: Path) -> tuple[Path, str]:
    """A project with two commits that each fix the code together with a test."""
    require("git")
    require("podman")
    ENGINES["podman"].pull(BUSYBOX)
    project = tmp_path / "project"
    project.mkdir()
    git(project, "init", "--quiet", "--initial-branch=main")
    commit(project, {"run.sh": RUN, "src/code.txt": "v0\n", "tests/test_v0.txt": "v0\n"}, 100)
    commit(project, {"src/code.txt": "v1\n", "tests/test_v1.txt": "v1\n"}, 200)
    last = commit(project, {"src/code.txt": "v2\n", "tests/test_v2.txt": "v2\n"}, 300)
    write_pack(project / ".dokime", '["sh", "/dokime/project/run.sh"]')
    return project, last


def dokime(*args: str, temporary: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "dokime.interfaces", *args],
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, "TMPDIR": str(temporary)},
        timeout=600,
    )


@pytest.fixture
def temporary(tmp_path: Path) -> Path:
    directory = tmp_path / "temporary"
    directory.mkdir()
    return directory


def test_a_pack_with_two_witnesses_passes_with_the_real_git_and_podman(
    project: tuple[Path, str], temporary: Path
) -> None:
    path, last = project
    before = ENGINES["podman"].containers()
    done = dokime("env", "check", "--from", last, "--project", str(path), temporary=temporary)
    lines = done.stdout.splitlines()
    assert done.returncode == 0, done.stdout + done.stderr
    assert lines[0].startswith("program git /")
    assert lines[1].startswith("program podman /")
    assert lines[2:4] == [
        f"candidate {last}: witness: tests::test_v2.txt",
        f"candidate {git(path, 'rev-parse', 'HEAD~1')}: witness: tests::test_v1.txt",
    ]
    assert lines[-1] == "PASS: no findings"
    assert ENGINES["podman"].containers() <= before
    assert list(temporary.iterdir()) == []


def test_a_full_name_that_is_not_a_commit_of_the_project_is_refused_by_the_adapter(
    project: tuple[Path, str], temporary: Path
) -> None:
    path, _ = project
    done = dokime("env", "check", "--from", "0" * 40, "--project", str(path), temporary=temporary)
    assert done.returncode == 2
    assert "ERROR unknown-commit" in done.stdout
    assert "not-a-commit-name" not in done.stdout


def test_a_project_that_is_not_a_repository_is_refused_on_opening(
    tmp_path: Path, temporary: Path
) -> None:
    require("git")
    require("podman")
    path = tmp_path / "not-a-repository"
    write_pack(path / ".dokime", '["true"]')
    done = dokime("env", "check", "--from", "a" * 40, "--project", str(path), temporary=temporary)
    assert done.returncode == 2
    assert "ERROR not-a-repository" in done.stdout
    assert "candidate" not in done.stdout


def running_containers() -> list[str]:
    """The containers of a run, which the adapter names `dokime-…`; a build has others."""
    listed = ENGINES["podman"].command("ps", "--filter", "name=^dokime-", "--format", "{{.Names}}")
    return listed.split()


@pytest.mark.parametrize("sent", [signal.SIGTERM, signal.SIGINT])
def test_an_interruption_in_the_middle_of_a_run_leaves_no_container_and_no_directory(
    project: tuple[Path, str], temporary: Path, sent: signal.Signals
) -> None:
    path, last = project
    slow = write_pack(path.parent / "slow", '["sleep", "120"]')
    engine = ENGINES["podman"]
    before = engine.containers()
    command = ["env", "check", "--from", last, "--project", str(path), "--pack", str(slow)]
    harness = subprocess.Popen(
        [sys.executable, "-m", "dokime.interfaces", *command],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env={**os.environ, "TMPDIR": str(temporary)},
    )
    try:
        deadline = time.monotonic() + 120
        while not running_containers():
            assert time.monotonic() < deadline, "the container of the run never started"
            assert harness.poll() is None, harness.communicate()
            time.sleep(0.2)
        harness.send_signal(sent)
        harness.communicate(timeout=60)
    finally:
        harness.kill()
    assert harness.returncode == -sent
    assert engine.containers() <= before
    assert list(temporary.iterdir()) == []
