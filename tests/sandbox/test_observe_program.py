# SDD-EARS: SANDBOX-090 SANDBOX-091 SANDBOX-092 SANDBOX-093 SANDBOX-094 SANDBOX-103
import os
from pathlib import Path

import pytest

from tests.sandbox.observing import function, observe, only, project

MODULE = """
import os

def pid():
    return os.getpid()

def here():
    names = sorted(os.listdir("."))
    with open("written.txt", "w") as handle:
        handle.write("x")
    return [os.getcwd(), names]
"""


@pytest.mark.parametrize("flags", [(), ("-I",), ("-S",)], ids=["none", "only-i", "only-s"])
def test_without_the_isolation_of_i_and_s_the_main_program_reads_nothing(
    tmp_path: Path, flags: tuple[str, ...]
) -> None:
    code = project(tmp_path / "code", {"proj.py": MODULE})
    run = observe(tmp_path, code, function("E-1", "proj:pid", {}), flags=flags)
    assert (run.code, run.observed) == (2, None)


def test_each_example_runs_in_a_child_of_its_own_and_its_steps_share_it(tmp_path: Path) -> None:
    code = project(tmp_path / "code", {"proj.py": MODULE})
    run = observe(
        tmp_path,
        code,
        function("E-1", "proj:pid", {}, {}),
        function("E-2", "proj:pid", {}),
    )
    assert run.observed is not None
    first, second = run.observed
    one, two = (step["returned"] for step in first["steps"])
    (three,) = (step["returned"] for step in second["steps"])
    assert one == two
    assert len({one, three, os.getpid()}) == 3


def test_each_example_has_an_empty_writable_working_directory_of_its_own(tmp_path: Path) -> None:
    code = project(tmp_path / "code", {"proj.py": MODULE})
    run = observe(
        tmp_path, code, function("E-1", "proj:here", {}), function("E-2", "proj:here", {})
    )
    assert run.observed is not None
    places = [example["steps"][0]["returned"] for example in run.observed]
    assert [names for _, names in places] == [[], []]
    assert places[0][0] != places[1][0]


def test_a_module_of_the_project_cannot_replace_one_that_the_child_loaded(tmp_path: Path) -> None:
    code = project(
        tmp_path / "code",
        {"json.py": "raise RuntimeError('the json of the project')\n", "proj.py": MODULE},
    )
    example = only(observe(tmp_path, code, function("E-1", "proj:pid", {})))
    assert example["ending"] == "completed"


def test_the_observations_of_every_example_are_written_to_one_file(tmp_path: Path) -> None:
    code = project(tmp_path / "code", {"proj.py": MODULE})
    run = observe(tmp_path, code, function("E-1", "proj:pid", {}), function("E-2", "proj:pid", {}))
    assert run.code == 0
    assert run.observed is not None
    assert [example["example"] for example in run.observed] == ["E-1", "E-2"]
