# SDD-EARS: SANDBOX-110 SANDBOX-111 SANDBOX-117 SANDBOX-118 SANDBOX-119
"""The podman adapter observes examples in a container of the image, through the program."""

import hashlib
from pathlib import Path

import pytest

from dokime.core.observation import (
    Boundary,
    Ending,
    ExampleObserver,
    ExampleRequest,
    Exited,
    ObservationLimits,
    Raised,
    Returned,
)
from dokime.core.runtime import BuildLimits, Digest, RunLimits
from dokime.sandbox.podman import PodmanRuntime
from tests.sandbox.engines import ENGINES, PYTHON, refusal, require

MODULE = """
import os
import time

def add(a, b):
    return a + b

def tenth():
    return 0.1

def write_probe():
    open("/dokime/probe/x", "w").write("x")

def big(n):
    return "x" * n

def hang():
    time.sleep(60)
"""


@pytest.fixture(scope="module")
def adapter() -> PodmanRuntime:
    require("podman")
    return PodmanRuntime()


@pytest.fixture(scope="module")
def image(adapter: PodmanRuntime, tmp_path_factory: pytest.TempPathFactory) -> Digest:
    context = tmp_path_factory.mktemp("context")
    ENGINES["podman"].pull(PYTHON)
    (context / "Dockerfile").write_text(f"FROM {PYTHON}\nENV PYTHONPATH=/dokime/project\n")
    return adapter.build(context / "Dockerfile", context, BuildLimits()).image


@pytest.fixture
def project(tmp_path: Path) -> Path:
    directory = tmp_path / "project"
    directory.mkdir()
    (directory / "proj.py").write_text(MODULE)
    return directory


def function(name: str, target: str, *inputs: dict[str, object]) -> ExampleRequest:
    return ExampleRequest(example=name, boundary=Boundary.FUNCTION, target=target, inputs=inputs)


def test_an_example_is_observed_in_a_container_of_the_image(
    adapter: PodmanRuntime, image: Digest, project: Path
) -> None:
    requests = (
        function("E-1", "proj:add", {"args": [2, 3]}),
        ExampleRequest(
            example="E-2", boundary=Boundary.CLI, target="python -c 'print(1)'", inputs=({},)
        ),
    )
    first, second = adapter.observe(image, project, requests, ObservationLimits())
    assert first.steps == (Returned(value=5),)
    assert second.steps == (Exited(exit=0, stdout="1\n", stderr="", files={}),)


def test_the_program_and_its_requests_are_read_only(
    adapter: PodmanRuntime, image: Digest, project: Path
) -> None:
    (observed,) = adapter.observe(
        image, project, (function("E-1", "proj:write_probe", {}),), ObservationLimits()
    )
    (step,) = observed.steps
    assert isinstance(step, Raised)
    assert "Read-only" in step.message


def test_each_example_gets_its_share_of_the_bytes_of_the_observations(
    adapter: PodmanRuntime, image: Digest, project: Path
) -> None:
    requests = (
        function("E-1", "proj:big", {"args": [3000]}),
        function("E-2", "proj:add", {"args": [1, 1]}),
    )
    big, small = adapter.observe(
        image, project, requests, ObservationLimits(observations_bytes=4000)
    )
    assert (big.ending, small.ending) == (Ending.OUTPUT_LIMIT, Ending.COMPLETED)


def test_a_decimal_returned_is_kept(adapter: PodmanRuntime, image: Digest, project: Path) -> None:
    (observed,) = adapter.observe(
        image, project, (function("E-1", "proj:tenth", {}),), ObservationLimits()
    )
    assert observed.steps == (Returned(value=0.1),)


def test_a_container_that_ends_at_its_limit_is_refused(
    adapter: PodmanRuntime, image: Digest, project: Path
) -> None:
    limits = ObservationLimits(run=RunLimits(time_seconds=3))
    finding = refusal(
        lambda: adapter.observe(image, project, (function("E-1", "proj:hang", {}),), limits)
    )
    assert finding.code == "observation-failed"


def test_a_program_that_ends_with_an_error_is_refused_quoting_it(
    adapter: PodmanRuntime, image: Digest, project: Path
) -> None:
    outside = ExampleRequest(
        example="E-1", boundary=Boundary.CLI, target="true", inputs=({"files": {"../x": "y"}},)
    )
    finding = refusal(lambda: adapter.observe(image, project, (outside,), ObservationLimits()))
    assert (finding.code, "outside the working directory" in finding.message) == (
        "observation-failed",
        True,
    )


def test_the_adapter_is_one_of_the_port_that_observes(adapter: PodmanRuntime) -> None:
    observer: ExampleObserver = adapter
    assert callable(observer.observe)


def test_the_adapter_gives_the_digest_of_the_program_it_mounts(adapter: PodmanRuntime) -> None:
    program = Path(__file__).parents[2] / "src" / "dokime" / "sandbox" / "observe_program.py"
    expected = "sha256:" + hashlib.sha256(program.read_bytes()).hexdigest()
    assert adapter.observe_program_digest == expected
