# SDD-EARS: SANDBOX-030 SANDBOX-031 SANDBOX-032 SANDBOX-034 SANDBOX-035 SANDBOX-036 SANDBOX-037
import stat
import threading
import time
from pathlib import Path

import pytest

from dokime.core.runtime import Digest, Ending, RunLimits, RunResult, VerificationRuntime
from dokime.sandbox.podman import PodmanRuntime
from tests.sandbox.engines import BUSYBOX, Engine

MIB = 1024 * 1024


@pytest.fixture
def directories(tmp_path: Path) -> tuple[Path, Path]:
    project, out = tmp_path / "project", tmp_path / "out"
    project.mkdir()
    out.mkdir()
    return project, out


def shell(
    engine: Engine,
    runtime: VerificationRuntime,
    directories: tuple[Path, Path],
    script: str,
    limits: RunLimits | None = None,
) -> RunResult:
    project, out = directories
    image = engine.pull(BUSYBOX)
    return runtime.run(image, ("sh", "-c", script), project, out, limits or RunLimits())


@pytest.mark.parametrize("code", [0, 1, 3, 126, 137, 255])
def test_a_command_that_ends_with_a_code_exits_with_it_137_included(
    engine: Engine, runtime: VerificationRuntime, directories: tuple[Path, Path], code: int
) -> None:
    result = shell(engine, runtime, directories, f"exit {code}")
    assert result == RunResult(ending=Ending.EXITED, exit_code=code)


def test_a_command_that_does_not_exist_exits_with_127(
    engine: Engine, runtime: VerificationRuntime, directories: tuple[Path, Path]
) -> None:
    project, out = directories
    result = runtime.run(engine.pull(BUSYBOX), ("no-such-command",), project, out, RunLimits())
    assert result == RunResult(ending=Ending.EXITED, exit_code=127)


def test_a_command_killed_by_the_memory_limit_ends_at_the_memory_limit(
    engine: Engine, runtime: VerificationRuntime, directories: tuple[Path, Path]
) -> None:
    limits = RunLimits(memory_bytes=64 * MIB)
    result = shell(engine, runtime, directories, "head -c 300m /dev/zero | tail", limits)
    assert result == RunResult(ending=Ending.MEMORY_LIMIT, exit_code=None)


def test_a_command_killed_from_outside_exits_with_137(
    engine: Engine, runtime: VerificationRuntime, directories: tuple[Path, Path]
) -> None:
    before = engine.containers()

    def kill_when_it_starts() -> None:
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            started = engine.containers() - before
            if started:
                engine.command("kill", "--signal", "KILL", *started, check=False)
                return
            time.sleep(0.2)

    killer = threading.Thread(target=kill_when_it_starts)
    killer.start()
    result = shell(engine, runtime, directories, "sleep 60")
    killer.join()
    assert result == RunResult(ending=Ending.EXITED, exit_code=137)


def test_a_command_that_passes_the_time_limit_ends_at_it_and_leaves_no_container(
    engine: Engine, runtime: VerificationRuntime, directories: tuple[Path, Path]
) -> None:
    before = engine.containers()
    start = time.monotonic()
    result = shell(engine, runtime, directories, "sleep 120", RunLimits(time_seconds=3))
    assert result == RunResult(ending=Ending.TIME_LIMIT, exit_code=None)
    assert time.monotonic() - start < 60
    assert engine.containers() <= before


@pytest.mark.parametrize("script", ["exit 0", "exit 5", "head -c 300m /dev/zero | tail"])
def test_a_run_leaves_no_container_whatever_its_ending(
    engine: Engine, runtime: VerificationRuntime, directories: tuple[Path, Path], script: str
) -> None:
    before = engine.containers()
    shell(engine, runtime, directories, script, RunLimits(memory_bytes=64 * MIB))
    assert engine.containers() <= before


def test_two_runs_at_once_each_get_a_container_of_their_own(
    engine: Engine, runtime: VerificationRuntime, tmp_path: Path
) -> None:
    results: list[RunResult] = []
    engine.pull(BUSYBOX)

    def one(index: int) -> None:
        project, out = tmp_path / f"p{index}", tmp_path / f"o{index}"
        project.mkdir()
        out.mkdir()
        results.append(shell(engine, runtime, (project, out), "sleep 2"))

    threads = [threading.Thread(target=one, args=(index,)) for index in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert results == [RunResult(ending=Ending.EXITED, exit_code=0)] * 2


@pytest.mark.parametrize("which", ["project", "output"])
def test_a_project_or_output_that_is_not_a_directory_is_rejected_naming_it(
    engine: Engine, runtime: VerificationRuntime, tmp_path: Path, which: str
) -> None:
    project, out = tmp_path / "project", tmp_path / "out"
    project.mkdir()
    out.mkdir()
    wrong = tmp_path / "not-a-directory"
    wrong.write_text("")
    arguments = (wrong, out) if which == "project" else (project, wrong)
    with pytest.raises(ValueError, match="not-a-directory"):
        runtime.run(engine.pull(BUSYBOX), ("true",), *arguments, RunLimits())
    missing = tmp_path / "missing"
    arguments = (missing, out) if which == "project" else (project, missing)
    with pytest.raises(ValueError, match="missing"):
        runtime.run(engine.pull(BUSYBOX), ("true",), *arguments, RunLimits())


def test_a_run_killed_by_the_memory_limit_leaves_the_working_directory_unchanged(
    engine: Engine,
    runtime: VerificationRuntime,
    directories: tuple[Path, Path],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    harness = tmp_path / "harness"
    harness.mkdir()
    monkeypatch.chdir(harness)
    limits = RunLimits(memory_bytes=64 * MIB)
    result = shell(engine, runtime, directories, "head -c 300m /dev/zero | tail", limits)
    assert result.ending is Ending.MEMORY_LIMIT
    assert list(harness.iterdir()) == []


@pytest.mark.parametrize("state", ["exited", "stopped"])
def test_a_container_that_has_exited_but_is_not_yet_cleaned_up_gives_its_exit_code(
    tmp_path: Path, state: str
) -> None:
    """Podman gives "stopped" for a container that has exited and is not yet cleaned up. Two runs
    at once can find it so after `podman run` returns."""
    program = tmp_path / "podman"
    program.write_text(
        "#!/bin/sh\n"
        'case "$1" in\n'
        '  --version) echo "podman version 5.4.2" ;;\n'
        f'  container) echo "{state} 3 false" ;;\n'
        "esac\n"
    )
    program.chmod(program.stat().st_mode | stat.S_IXUSR)
    project, out = tmp_path / "project", tmp_path / "out"
    project.mkdir()
    out.mkdir()
    runtime = PodmanRuntime(podman=str(program))
    result = runtime.run(Digest(f"sha256:{'a' * 64}"), ("true",), project, out, RunLimits())
    assert result == RunResult(ending=Ending.EXITED, exit_code=3)
