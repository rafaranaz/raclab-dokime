# SDD-EARS: SANDBOX-025 SANDBOX-026 SANDBOX-027 SANDBOX-028
import os
from pathlib import Path

import pytest

from dokime.core.runtime import Ending, RunLimits, RunResult, VerificationRuntime
from tests.sandbox.engines import BUSYBOX, Engine


@pytest.fixture
def directories(tmp_path: Path) -> tuple[Path, Path]:
    project, out = tmp_path / "project", tmp_path / "out"
    project.mkdir()
    out.mkdir()
    (project / "data").write_text("of the project\n")
    return project, out


def shell(
    engine: Engine, runtime: VerificationRuntime, directories: tuple[Path, Path], script: str
) -> RunResult:
    project, out = directories
    return runtime.run(engine.pull(BUSYBOX), ("sh", "-c", script), project, out, RunLimits())


def test_the_project_is_mounted_read_only_as_the_working_directory(
    engine: Engine, runtime: VerificationRuntime, directories: tuple[Path, Path]
) -> None:
    script = "cat data > /dokime/out/read; pwd > /dokime/out/where; echo x > written"
    result = shell(engine, runtime, directories, script)
    project, out = directories
    assert result.ending is Ending.EXITED
    assert result.exit_code != 0
    assert (out / "read").read_text() == "of the project\n"
    assert (out / "where").read_text() == "/dokime/project\n"
    assert sorted(path.name for path in project.iterdir()) == ["data"]


def test_the_output_directory_is_mounted_writable(
    engine: Engine, runtime: VerificationRuntime, directories: tuple[Path, Path]
) -> None:
    result = shell(
        engine, runtime, directories, "mkdir /dokime/out/deep && echo y > /dokime/out/deep/f"
    )
    assert result == RunResult(ending=Ending.EXITED, exit_code=0)
    assert (directories[1] / "deep" / "f").read_text() == "y\n"


def test_tmp_is_writable_and_not_kept_after_the_run(
    engine: Engine, runtime: VerificationRuntime, directories: tuple[Path, Path]
) -> None:
    assert (
        shell(engine, runtime, directories, "echo t > /tmp/kept && test -f /tmp/kept").exit_code
        == 0
    )
    assert shell(engine, runtime, directories, "test ! -e /tmp/kept").exit_code == 0


def test_the_files_written_in_the_output_belong_to_the_user_who_runs_the_harness(
    engine: Engine, runtime: VerificationRuntime, directories: tuple[Path, Path]
) -> None:
    shell(engine, runtime, directories, "echo z > /dokime/out/owned && mkdir /dokime/out/dir")
    out = directories[1]
    assert {(out / name).stat().st_uid for name in ("owned", "dir")} == {os.getuid()}
