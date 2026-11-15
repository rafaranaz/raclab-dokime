# SDD-EARS: SANDBOX-038
"""Only an image that runs as root is run: in a rootless engine, root in the container is the
person who runs the harness, and any other user could not write in the output."""

from pathlib import Path

import pytest

from dokime.core.runtime import (
    BuildLimits,
    Digest,
    Ending,
    RunLimits,
    RunResult,
    VerificationRuntime,
)
from tests.sandbox.engines import BUSYBOX, Engine, refusal


def image_with_user(tmp_path: Path, runtime: VerificationRuntime, user: str | None) -> Digest:
    directory = tmp_path / "context"
    directory.mkdir()
    line = f"USER {user}\n" if user is not None else ""
    (directory / "Dockerfile").write_text(f"FROM {BUSYBOX}\n{line}")
    return runtime.build(directory / "Dockerfile", directory, BuildLimits()).image


def directories(tmp_path: Path) -> tuple[Path, Path]:
    project, out = tmp_path / "project", tmp_path / "out"
    project.mkdir()
    out.mkdir()
    return project, out


@pytest.mark.parametrize("user", [None, "0", "root", "0:0", "root:root"])
def test_an_image_that_runs_as_root_is_run(
    tmp_path: Path, engine: Engine, runtime: VerificationRuntime, user: str | None
) -> None:
    engine.pull(BUSYBOX)
    image = image_with_user(tmp_path, runtime, user)
    project, out = directories(tmp_path)
    result = runtime.run(image, ("sh", "-c", "echo z > /dokime/out/f"), project, out, RunLimits())
    assert result == RunResult(ending=Ending.EXITED, exit_code=0)
    assert (out / "f").read_text() == "z\n"


@pytest.mark.parametrize("user", ["1000", "1000:1000", "tester", "root:1000", "nobody:root"])
def test_an_image_that_runs_as_another_user_is_refused_before_running_anything(
    tmp_path: Path, engine: Engine, runtime: VerificationRuntime, user: str
) -> None:
    engine.pull(BUSYBOX)
    image = image_with_user(tmp_path, runtime, user)
    project, out = directories(tmp_path)
    before = engine.containers()
    finding = refusal(lambda: runtime.run(image, ("true",), project, out, RunLimits()))
    assert finding.code == "user-not-root"
    assert repr(user) in finding.message
    assert "base image" in finding.message
    assert "Dockerfile of the pack" in finding.message
    assert engine.containers() <= before
