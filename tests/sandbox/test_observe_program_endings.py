# SDD-EARS: SANDBOX-095 SANDBOX-096
import os
import time
from pathlib import Path

from tests.sandbox.observing import function, observe, only, project

MODULE = """
import os
import signal
import subprocess
import time

def quick():
    return 1

def hang(pids):
    child = subprocess.Popen(["sleep", "60"])
    with open(pids, "w") as handle:
        handle.write(str(child.pid))
    time.sleep(60)

def killed():
    os.kill(os.getpid(), signal.SIGKILL)

def exits():
    os._exit(5)
"""


def alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    return Path(f"/proc/{pid}/stat").read_text().split()[2] != "Z"


def test_an_example_that_hangs_reaches_its_limit_and_keeps_the_steps_before(
    tmp_path: Path,
) -> None:
    code = project(tmp_path / "code", {"proj.py": MODULE})
    pids = tmp_path / "pids"
    started = time.monotonic()
    run = observe(
        tmp_path / "again",
        code,
        {
            "example": "E-3",
            "boundary": "function",
            "target": "proj:hang",
            "inputs": [{"args": [str(pids)]}],
        },
        function("E-4", "proj:quick", {}),
        seconds=2,
    )
    assert run.observed is not None
    hung, after = run.observed
    assert (hung["ending"], hung["steps"]) == ("time-limit", [])
    assert after["ending"] == "completed"
    assert time.monotonic() - started < 30
    assert not alive(int(pids.read_text()))


def test_a_step_before_the_one_that_hangs_is_kept(tmp_path: Path) -> None:
    code = project(
        tmp_path / "code",
        {"proj.py": MODULE + "\ndef step(n):\n    if n: time.sleep(60)\n    return n\n"},
    )
    example = only(
        observe(
            tmp_path, code, function("E-1", "proj:step", {"args": [0]}, {"args": [1]}), seconds=2
        )
    )
    assert (example["ending"], example["steps"]) == ("time-limit", [{"returned": 0}])


def test_an_example_killed_by_a_signal_is_crashed_with_the_signal(tmp_path: Path) -> None:
    code = project(tmp_path / "code", {"proj.py": MODULE})
    example = only(observe(tmp_path, code, function("E-1", "proj:killed", {})))
    assert (example["ending"], example["signal"]) == ("crashed", 9)


def test_an_example_that_exits_before_its_last_step_is_crashed_with_the_code(
    tmp_path: Path,
) -> None:
    code = project(tmp_path / "code", {"proj.py": MODULE})
    example = only(observe(tmp_path, code, function("E-1", "proj:exits", {}, {})))
    assert (example["ending"], example["exit_code"], example["steps"]) == ("crashed", 5, [])


def test_an_example_whose_target_cannot_be_imported_is_crashed(tmp_path: Path) -> None:
    code = project(tmp_path / "code", {"proj.py": MODULE})
    example = only(observe(tmp_path, code, function("E-1", "absent:f", {})))
    assert (example["ending"], example["exit_code"]) == ("crashed", 3)
