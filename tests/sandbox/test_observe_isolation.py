# SDD-EARS: SANDBOX-126 SANDBOX-127
"""Nothing that one example leaves reaches the next: the probes that found that it did, kept as
tests on the podman adapter (ADR-0080)."""

from pathlib import Path

import pytest

from dokime.core.observation import (
    Boundary,
    Ending,
    ExampleObservation,
    ExampleRequest,
    ObservationLimits,
    Returned,
)
from dokime.core.runtime import BuildLimits, Digest
from dokime.sandbox.podman import PodmanRuntime
from tests.sandbox.engines import ENGINES, PYTHON, require

MODULE = r"""
import ctypes
import ctypes.util
import subprocess
import time

STATE = "left by the first example"
WRITER = "import time\nwhile True:\n    open('/tmp/alive', 'a').write('.'); time.sleep(0.05)"
KEY = 0x00D0C1E0
libc = ctypes.CDLL(ctypes.util.find_library("c"), use_errno=True)
libc.shmat.restype = ctypes.c_void_p
libc.syscall.restype = ctypes.c_long


def write_file(place):
    with open(place + "/dokime-state", "w") as handle:
        handle.write(STATE)
    return "written"


def read_file(place):
    try:
        with open(place + "/dokime-state") as handle:
            return handle.read()
    except OSError:
        return None


def leave_a_process():
    subprocess.Popen(
        ["python", "-c", WRITER],
        start_new_session=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    time.sleep(0.3)
    return "left"


def find_the_process():
    time.sleep(0.3)
    try:
        before = len(open("/tmp/alive").read())
    except OSError:
        return None
    time.sleep(0.3)
    return len(open("/tmp/alive").read()) - before


def write_sysv():
    shm = libc.shmget(KEY, 64, 0o1000 | 0o666)
    address = libc.shmat(shm, None, 0)
    ctypes.memmove(address, STATE.encode() + b"\0", len(STATE) + 1)
    sem = libc.semget(KEY, 1, 0o1000 | 0o666)
    libc.semctl(sem, 0, 16, ctypes.c_int(4242))
    return "written"


def read_sysv():
    shm, sem = libc.shmget(KEY, 64, 0), libc.semget(KEY, 1, 0)
    return [shm >= 0, sem >= 0]


def write_key():
    return libc.syscall(248, b"user", b"dokime-state", STATE.encode(), len(STATE), -4) >= 0


def read_key():
    return libc.syscall(249, b"user", b"dokime-state", None, -4) >= 0


def sleep(seconds):
    time.sleep(seconds)
    return "slept"
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
    (directory / "probe.py").write_text(MODULE)
    return directory


def call(name: str, target: str, *args: object) -> ExampleRequest:
    return ExampleRequest(
        example=name, boundary=Boundary.FUNCTION, target=target, inputs=({"args": list(args)},)
    )


def second(
    adapter: PodmanRuntime, image: Digest, project: Path, *requests: ExampleRequest
) -> object:
    observed: tuple[ExampleObservation, ...] = adapter.observe(
        image, project, requests, ObservationLimits()
    )
    (step,) = observed[-1].steps
    assert isinstance(step, Returned), step
    return step.value


@pytest.mark.parametrize("place", ["/tmp", "/dokime/out"])  # noqa: S108 - a place in the container
def test_a_file_that_one_example_writes_is_not_seen_by_the_next(
    adapter: PodmanRuntime, image: Digest, project: Path, place: str
) -> None:
    requests = (call("E-1", "probe:write_file", place), call("E-2", "probe:read_file", place))
    assert second(adapter, image, project, *requests) is None


def test_a_process_that_one_example_leaves_is_not_running_in_the_next(
    adapter: PodmanRuntime, image: Digest, project: Path
) -> None:
    requests = (call("E-1", "probe:leave_a_process"), call("E-2", "probe:find_the_process"))
    assert second(adapter, image, project, *requests) is None


def test_system_v_memory_and_semaphores_of_one_example_are_not_in_the_next(
    adapter: PodmanRuntime, image: Digest, project: Path
) -> None:
    requests = (call("E-1", "probe:write_sysv"), call("E-2", "probe:read_sysv"))
    assert second(adapter, image, project, *requests) == [False, False]


def test_a_key_of_one_example_is_not_in_the_keyring_of_the_next(
    adapter: PodmanRuntime, image: Digest, project: Path
) -> None:
    requests = (call("E-1", "probe:write_key"), call("E-2", "probe:read_key"))
    assert second(adapter, image, project, *requests) is False


def test_the_time_limit_of_an_example_does_not_count_the_start_of_its_container(
    adapter: PodmanRuntime, image: Digest, project: Path
) -> None:
    limits = ObservationLimits(example_seconds=1)
    # The child starts Python and imports within its limit; the container starts outside it.
    (observed,) = adapter.observe(image, project, (call("E-1", "probe:sleep", 0.4),), limits)
    assert observed.ending is Ending.COMPLETED
    assert observed.steps == (Returned("slept"),)
