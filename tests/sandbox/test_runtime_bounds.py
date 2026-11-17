# SDD-EARS: SANDBOX-029 SANDBOX-039
"""The writable places of a run are bounded: `/tmp` in size, and every file in bytes."""

from pathlib import Path

import pytest

from dokime.core.runtime import Ending, RunLimits, VerificationRuntime
from tests.sandbox.engines import BUSYBOX, Engine

MIB = 1024 * 1024


@pytest.fixture
def directories(tmp_path: Path) -> tuple[Path, Path]:
    project, out = tmp_path / "project", tmp_path / "out"
    project.mkdir()
    out.mkdir()
    return project, out


def run(
    engine: Engine,
    runtime: VerificationRuntime,
    directories: tuple[Path, Path],
    script: str,
    limits: RunLimits,
) -> tuple[Ending, int | None, str]:
    project, out = directories
    result = runtime.run(engine.pull(BUSYBOX), ("sh", "-c", script), project, out, limits)
    said = out / "said"
    return result.ending, result.exit_code, said.read_text() if said.exists() else ""


def test_filling_tmp_fails_on_its_size_and_not_on_the_memory(
    engine: Engine, runtime: VerificationRuntime, directories: tuple[Path, Path]
) -> None:
    limits = RunLimits(memory_bytes=128 * MIB)
    script = "dd if=/dev/zero of=/tmp/fill bs=1M count=50 2>/dokime/out/said; exit 7"
    ending, code, said = run(engine, runtime, directories, script, limits)
    assert (ending, code) == (Ending.EXITED, 7)
    assert "No space left" in said


def test_a_quarter_of_the_memory_fits_in_tmp(
    engine: Engine, runtime: VerificationRuntime, directories: tuple[Path, Path]
) -> None:
    limits = RunLimits(memory_bytes=256 * MIB)
    script = "dd if=/dev/zero of=/tmp/fill bs=1M count=60 2>/dokime/out/said"
    assert run(engine, runtime, directories, script, limits)[:2] == (Ending.EXITED, 0)


def test_a_file_written_in_the_output_stops_at_64_mib(
    engine: Engine, runtime: VerificationRuntime, directories: tuple[Path, Path]
) -> None:
    script = "dd if=/dev/zero of=/dokime/out/big bs=1M count=70; echo $? > /dokime/out/said"
    ending, _, _ = run(engine, runtime, directories, script, RunLimits())
    assert ending is Ending.EXITED
    assert (directories[1] / "big").stat().st_size == 64 * MIB


def test_a_file_under_64_mib_is_written_whole(
    engine: Engine, runtime: VerificationRuntime, directories: tuple[Path, Path]
) -> None:
    script = "dd if=/dev/zero of=/dokime/out/big bs=1M count=60"
    assert run(engine, runtime, directories, script, RunLimits())[:2] == (Ending.EXITED, 0)
    assert (directories[1] / "big").stat().st_size == 60 * MIB
