# SDD-EARS: SANDBOX-020 SANDBOX-021 SANDBOX-022 SANDBOX-023 SANDBOX-024
"""The four guarantees of ADR-0043, proven with a load and not by reading the options passed.

Each limit is shown to stop the load, and a wider limit is shown to let the same load through, so
that what stops it is the limit and not the load.
"""

from pathlib import Path

import pytest

from dokime.core.runtime import Ending, RunLimits, RunResult, VerificationRuntime
from tests.sandbox.engines import PYTHON, Engine

LOAD = Path(__file__).with_name("load.py")
MIB = 1024 * 1024


@pytest.fixture
def directories(tmp_path: Path) -> tuple[Path, Path]:
    project, out = tmp_path / "project", tmp_path / "out"
    project.mkdir()
    out.mkdir()
    (project / "load.py").write_bytes(LOAD.read_bytes())
    return project, out


def load(
    engine: Engine,
    runtime: VerificationRuntime,
    directories: tuple[Path, Path],
    limits: RunLimits,
    *args: str,
) -> tuple[RunResult, str]:
    project, out = directories
    command = ("python", "/dokime/project/load.py", *args)
    result = runtime.run(engine.pull(PYTHON), command, project, out, limits)
    written = out / "result"
    return result, written.read_text() if written.exists() else ""


def test_a_command_has_no_network(
    engine: Engine, runtime: VerificationRuntime, directories: tuple[Path, Path]
) -> None:
    result, measured = load(engine, runtime, directories, RunLimits(), "network")
    assert result == RunResult(ending=Ending.EXITED, exit_code=0)
    assert measured.startswith("refused")


def test_a_command_is_killed_when_its_memory_with_swap_passes_the_limit(
    engine: Engine, runtime: VerificationRuntime, directories: tuple[Path, Path]
) -> None:
    tight = RunLimits(memory_bytes=256 * MIB)
    result, measured = load(engine, runtime, directories, tight, "memory", "600")
    assert result == RunResult(ending=Ending.MEMORY_LIMIT, exit_code=None)
    assert measured == ""
    wide = RunLimits(memory_bytes=1024 * MIB)
    result, measured = load(engine, runtime, directories, wide, "memory", "300")
    assert (result.ending, measured) == (Ending.EXITED, "allocated 300")


def test_a_command_uses_no_more_processor_than_its_limit(
    engine: Engine, runtime: VerificationRuntime, directories: tuple[Path, Path]
) -> None:
    _, measured = load(
        engine, runtime, directories, RunLimits(processors=0.5), "processor", "4", "4"
    )
    assert float(measured.split()[1]) <= 0.5 * 1.2
    _, measured = load(engine, runtime, directories, RunLimits(processors=2), "processor", "4", "4")
    assert float(measured.split()[1]) > 0.5 * 1.5


def test_a_command_starts_no_more_processes_and_threads_than_its_limit(
    engine: Engine, runtime: VerificationRuntime, directories: tuple[Path, Path]
) -> None:
    _, measured = load(engine, runtime, directories, RunLimits(processes=64), "processes", "200")
    assert int(measured.split()[1]) < 64
    _, measured = load(engine, runtime, directories, RunLimits(processes=512), "processes", "200")
    assert measured == "started 200"


def test_the_root_of_the_container_is_read_only(
    engine: Engine, runtime: VerificationRuntime, directories: tuple[Path, Path]
) -> None:
    _, measured = load(engine, runtime, directories, RunLimits(), "write", "/etc/written")
    assert measured == "refused OSError"
