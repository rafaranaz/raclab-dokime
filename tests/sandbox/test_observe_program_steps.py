# SDD-EARS: SANDBOX-097 SANDBOX-098 SANDBOX-099 SANDBOX-100 SANDBOX-101 SANDBOX-102
import shlex
import sys
from pathlib import Path
from typing import Any

import pytest

from tests.sandbox.observing import cli, function, observe, only, project

MODULE = """
def give(value):
    return value

def tuple_of(a, b):
    return (a, b)

def a_set():
    return {1, 2}

def nan():
    return float("nan")

def fails(part=None):
    from proj_errors import BadPart
    raise BadPart(f"bad {part}")
"""
ERRORS = "class BadPart(TypeError):\n    pass\n"


def steps(tmp_path: Path, *examples: dict[str, Any]) -> list[Any]:
    code = project(tmp_path / "code", {"proj.py": MODULE, "proj_errors.py": ERRORS})
    observed: list[Any] = only(observe(tmp_path, code, *examples))["steps"]
    return observed


def test_a_value_that_json_holds_is_observed_as_returned(tmp_path: Path) -> None:
    value = {"a": [1, 2.5, None, "é", True]}
    assert steps(tmp_path, function("E", "proj:give", {"args": [value]})) == [{"returned": value}]


def test_a_tuple_is_observed_as_the_list_that_json_holds(tmp_path: Path) -> None:
    observed = steps(tmp_path, function("E", "proj:tuple_of", {"args": [1, "x"]}))
    assert observed == [{"returned": [1, "x"]}]


@pytest.mark.parametrize(("target", "kind"), [("proj:a_set", "set"), ("proj:nan", "float")])
def test_a_value_that_json_cannot_hold_is_observed_by_its_type(
    tmp_path: Path, target: str, kind: str
) -> None:
    assert steps(tmp_path, function("E", target, {})) == [{"not_json": kind}]


def test_an_exception_is_observed_with_its_classes_and_its_message(tmp_path: Path) -> None:
    (step,) = steps(tmp_path, function("E", "proj:fails", {"kwargs": {"part": "major"}}))
    assert step == {
        "raised": {
            "type": "BadPart",
            "qualified": "proj_errors.BadPart",
            "classes": [
                "proj_errors.BadPart",
                "builtins.TypeError",
                "builtins.Exception",
                "builtins.BaseException",
                "builtins.object",
            ],
            "message": "bad major",
        }
    }


SCRIPT = """
import os, sys
data = sys.stdin.read()
given = open("given.txt").read()
open("out.txt", "w").write(data.upper() + given + os.environ["EXTRA"])
os.symlink("/etc/hostname", "linked.txt")
sys.stdout.buffer.write(b"ok \\xff")
sys.stderr.write(" ".join(sys.argv[1:]))
sys.exit(3)
"""


def test_a_step_at_cli_runs_its_command_with_its_inputs(tmp_path: Path) -> None:
    script = tmp_path / "script.py"
    script.write_text(SCRIPT)
    target = f"{shlex.quote(sys.executable)} {shlex.quote(str(script))}"
    step: dict[str, Any] = {
        "args": ["a", "b c"],
        "stdin": "in",
        "env": {"EXTRA": "!"},
        "files": {"given.txt": "g"},
    }
    (observed,) = steps(tmp_path, cli("E", target, step))
    assert observed == {
        "exit": 3,
        "stdout": "ok �",
        "stderr": "a b c",
        "files": {"given.txt": "g", "out.txt": "INg!"},
    }


def test_the_files_of_a_step_are_read_without_following_a_link(tmp_path: Path) -> None:
    script = tmp_path / "script.py"
    script.write_text(SCRIPT)
    target = f"{shlex.quote(sys.executable)} {shlex.quote(str(script))}"
    step: dict[str, Any] = {"stdin": "", "env": {"EXTRA": ""}, "files": {"given.txt": ""}}
    (observed,) = steps(tmp_path, cli("E", target, step))
    assert "linked.txt" not in observed["files"]
