# SDD-EARS: SANDBOX-104 SANDBOX-105 SANDBOX-106 SANDBOX-107 SANDBOX-108
import shlex
import sys
from pathlib import Path
from typing import Any

import pytest

from tests.sandbox.observing import cli, function, observe, project

MODULE = """
import os
import sys

def one():
    return 1

def garbage():
    os.write(int(sys.argv[2]), b'{"returned": 1}\\n{"cut')
    os._exit(0)

def deep():
    os.write(int(sys.argv[2]), b"[" * 100000 + b"\\n")
    return 1

def flood():
    while True:
        os.write(int(sys.argv[2]), b'{"returned": "' + b"x" * 60000 + b'"}\\n')

class Unprintable(Exception):
    def __str__(self):
        raise RuntimeError("no")

def unprintable():
    raise Unprintable()
"""


def run(tmp_path: Path, *examples: dict[str, Any], limit: int = 1_000_000) -> list[Any]:
    code = project(tmp_path / "code", {"proj.py": MODULE})
    done = observe(tmp_path, code, *examples, limit=limit)
    assert done.observed is not None
    return done.observed


def test_a_line_that_is_not_json_crashes_its_example_and_the_next_goes_on(tmp_path: Path) -> None:
    broken, after = run(
        tmp_path, function("E-1", "proj:garbage", {}, {}), function("E-2", "proj:one", {})
    )
    assert (broken["ending"], broken["steps"]) == ("crashed", [{"returned": 1}])
    assert after["ending"] == "completed"


def test_a_line_nested_too_deep_crashes_its_example(tmp_path: Path) -> None:
    (deep,) = run(tmp_path, function("E-1", "proj:deep", {}))
    assert deep["ending"] == "crashed"


def test_a_child_that_writes_past_its_bytes_reaches_its_limit_of_output(tmp_path: Path) -> None:
    flooded, after = run(
        tmp_path, function("E-1", "proj:flood", {}), function("E-2", "proj:one", {}), limit=200_000
    )
    assert flooded["ending"] == "output-limit"
    assert after["ending"] == "completed"


@pytest.mark.parametrize(
    "script",
    [
        "import sys; sys.stdout.write('x' * 300000)",
        "import sys; sys.stderr.write('x' * 300000)",
        "open('big.txt', 'w').write('x' * 300000)",
    ],
    ids=["stdout", "stderr", "a-file"],
)
def test_a_command_whose_output_passes_the_bytes_reaches_the_limit(
    tmp_path: Path, script: str
) -> None:
    target = f"{shlex.quote(sys.executable)} -c {shlex.quote(script)}"
    (example,) = run(tmp_path, cli("E-1", target, {}), limit=200_000)
    assert example["ending"] == "output-limit"


@pytest.mark.parametrize("name", ["../../out/observations.json", "/absolute/x", "a/../b"])
def test_a_file_named_outside_the_working_directory_ends_the_program(
    tmp_path: Path, name: str
) -> None:
    code = project(tmp_path / "code", {"proj.py": MODULE})
    done = observe(tmp_path, code, cli("E-1", "true", {"files": {name: "x"}}))
    assert (done.code, done.observed) == (2, None)


def test_an_exception_whose_message_cannot_be_read_is_still_observed(tmp_path: Path) -> None:
    (example,) = run(tmp_path, function("E-1", "proj:unprintable", {}))
    (step,) = example["steps"]
    assert (example["ending"], step["raised"]["type"]) == ("completed", "Unprintable")
    assert "cannot be read" in step["raised"]["message"]
