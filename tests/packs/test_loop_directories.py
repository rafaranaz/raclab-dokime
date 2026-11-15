# SDD-EARS: PACKS-080 PACKS-081
"""The directories of each side live under the temporary directory and are removed, on an
interruption too. The interruption is sent to a self-check that runs in a process of its own."""

import os
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import pytest

from tests.packs.doubles import FakeRepository, FakeRuntime
from tests.packs.loops import fixing_commit, root, self_check


@pytest.fixture
def temporary(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    directory = tmp_path / "temporary"
    directory.mkdir()
    monkeypatch.setattr(tempfile, "tempdir", str(directory))
    return directory


def test_the_directories_of_each_side_are_removed_after_it_runs(
    tmp_path: Path, temporary: Path
) -> None:
    repository = FakeRepository()
    one = fixing_commit(repository, root(repository), "one", 200)
    seen: list[list[str]] = []

    def look(project: Path, output: Path) -> None:
        seen.append(sorted(p.name for p in temporary.iterdir()))

    self_check(tmp_path, repository, FakeRuntime(while_running=look), one)
    assert len(seen) == 2
    assert all(len(names) >= 1 for names in seen)
    assert len(repository.extracted) == 2
    assert not any(directory.exists() for directory in repository.extracted)
    assert list(temporary.iterdir()) == []


HARNESS = """
import sys, time
from pathlib import Path
import tempfile
tempfile.tempdir = sys.argv[1]
from tests.packs.doubles import FakeRepository, FakeRuntime
from tests.packs.loops import fixing_commit, root, self_check

def wait(project, output):
    (Path(sys.argv[2]) / "running").write_text(str(project))
    time.sleep(120)

repository = FakeRepository()
one = fixing_commit(repository, root(repository), "one", 200)
self_check(Path(sys.argv[2]), repository, FakeRuntime(while_running=wait), one)
print("the self-check returned", flush=True)
"""


@pytest.mark.parametrize("sent", [signal.SIGINT, signal.SIGTERM])
def test_an_interruption_removes_the_directories_of_the_side_and_goes_on(
    tmp_path: Path, temporary: Path, sent: signal.Signals
) -> None:
    work = tmp_path / "work"
    work.mkdir()
    harness = subprocess.Popen(
        [sys.executable, "-c", HARNESS, str(temporary), str(work)],
        cwd=Path(__file__).parents[2],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env={**os.environ, "PYTHONPATH": str(Path(__file__).parents[2])},
    )
    try:
        deadline = time.monotonic() + 60
        while not (work / "running").exists():
            assert time.monotonic() < deadline, "the side never started"
            assert harness.poll() is None, harness.communicate()
            time.sleep(0.05)
        assert Path((work / "running").read_text()).exists()
        harness.send_signal(sent)
        stdout, _ = harness.communicate(timeout=60)
    finally:
        harness.kill()
    assert harness.returncode == -sent
    assert "the self-check returned" not in stdout
    assert list(temporary.iterdir()) == []
