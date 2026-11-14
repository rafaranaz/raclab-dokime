# SDD-EARS: CORE-081 CORE-082 CORE-083 CORE-084 CORE-085 CORE-086 CORE-087 CORE-088 CORE-089
from pathlib import Path, PurePosixPath
from typing import get_type_hints

import pytest

from dokime.core.outcomes import Report, ReportLimits
from dokime.core.repository import RefusalError
from dokime.core.runtime import (
    BaseImage,
    Build,
    BuildLimits,
    Digest,
    Ending,
    RunLimits,
    RunResult,
    VerificationRuntime,
)

HEX = "0123456789abcdef" * 4
IMAGE = Digest(f"sha256:{HEX}")
OTHER = Digest(f"sha256:{'f' * 64}")


def test_the_port_offers_the_three_operations() -> None:
    public = {name for name in vars(VerificationRuntime) if not name.startswith("_")}
    assert public == {"build", "run", "read_report"}


def test_the_build_receives_the_dockerfile_the_directory_and_its_limits() -> None:
    hints = get_type_hints(VerificationRuntime.build)
    assert (hints["dockerfile"], hints["directory"], hints["limits"]) == (Path, Path, BuildLimits)


def test_the_build_returns_the_image_and_the_base_image_of_the_final_stage_or_none() -> None:
    assert get_type_hints(VerificationRuntime.build)["return"] is Build
    built = Build(image=IMAGE, base=None)
    assert (built.image, built.base) == (IMAGE, None)
    assert get_type_hints(Build)["base"] == BaseImage | None


def test_the_base_image_carries_the_reference_the_platform_digest_and_the_index_digest() -> None:
    base = BaseImage(reference="python:3.13-slim", platform=IMAGE, index=OTHER)
    assert (base.reference, base.platform, base.index) == ("python:3.13-slim", IMAGE, OTHER)
    assert BaseImage(reference="python:3.13-slim", platform=IMAGE, index=None).index is None
    assert get_type_hints(BaseImage)["index"] == Digest | None


def test_the_run_receives_the_image_the_command_the_directories_and_its_limits() -> None:
    hints = get_type_hints(VerificationRuntime.run)
    assert hints["image"] is Digest
    assert hints["command"] == tuple[str, ...]
    assert (hints["project"], hints["output"], hints["limits"]) == (Path, Path, RunLimits)
    assert hints["return"] is RunResult


def test_a_run_ends_in_one_of_four_ways() -> None:
    assert {ending.value for ending in Ending} == {
        "exited",
        "time-limit",
        "memory-limit",
        "killed",
    }


def test_a_run_that_exited_by_itself_carries_its_exit_code() -> None:
    assert RunResult(ending=Ending.EXITED, exit_code=3).exit_code == 3
    assert RunResult(ending=Ending.EXITED, exit_code=0).exit_code == 0


def test_a_run_that_exited_by_itself_without_an_exit_code_is_rejected() -> None:
    with pytest.raises(ValueError, match="exit code"):
        RunResult(ending=Ending.EXITED, exit_code=None)


@pytest.mark.parametrize("ending", [Ending.TIME_LIMIT, Ending.MEMORY_LIMIT, Ending.KILLED])
def test_a_run_that_was_killed_carries_no_exit_code(ending: Ending) -> None:
    assert RunResult(ending=ending, exit_code=None).exit_code is None
    with pytest.raises(ValueError, match="exit code"):
        RunResult(ending=ending, exit_code=137)


def test_reading_a_report_receives_the_output_the_path_and_the_limits_and_gives_the_report() -> (
    None
):
    hints = get_type_hints(VerificationRuntime.read_report)
    assert (hints["output"], hints["report"], hints["limits"]) == (
        Path,
        PurePosixPath,
        ReportLimits,
    )
    assert hints["return"] == Report


def test_the_runtime_refuses_with_the_refusal_of_the_project_repository() -> None:
    from dokime.core import runtime

    assert runtime.RefusalError is RefusalError
