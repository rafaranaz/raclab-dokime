# SDD-EARS: SANDBOX-120 SANDBOX-121 SANDBOX-122 SANDBOX-123 SANDBOX-124
from pathlib import Path
from typing import Any

from tests.sandbox.observing import function, observe, only, project

MODULE = """
class Counter:
    def __init__(self, start):
        self.value = start

    def add(self, amount):
        self.value += amount
        return self.value

    def fail(self):
        raise ValueError("no")

    def __len__(self):
        return self.value

    def __repr__(self):
        return f"Counter({self.value})"


class Long:
    def __repr__(self):
        return "x" * 5000


class Broken:
    def __repr__(self):
        raise RuntimeError("no repr")


def refuse(value):
    raise TypeError(value)
"""


def steps(tmp_path: Path, *inputs: dict[str, Any], target: str = "proj:Counter") -> list[Any]:
    code = project(tmp_path / "code", {"proj.py": MODULE})
    observed: list[Any] = only(observe(tmp_path, code, function("E", target, *inputs)))["steps"]
    return observed


def test_a_step_with_call_calls_the_method_of_what_the_first_step_returned(tmp_path: Path) -> None:
    seen = steps(
        tmp_path,
        {"args": [1]},
        {"call": "add", "args": [2]},
        {"call": "add", "kwargs": {"amount": 3}},
        {"call": "__len__"},
    )
    assert seen[1:] == [{"returned": 3}, {"returned": 6}, {"returned": 6}]


def test_a_call_that_raises_is_observed_and_the_next_steps_run(tmp_path: Path) -> None:
    seen = steps(
        tmp_path, {"args": [1]}, {"call": "fail"}, {"call": "missing"}, {"call": "add", "args": [1]}
    )
    assert seen[1]["raised"]["qualified"] == "builtins.ValueError"
    assert seen[2]["raised"]["qualified"] == "builtins.AttributeError"
    assert seen[3] == {"returned": 2}


def test_no_step_is_observed_after_a_first_step_that_did_not_return(tmp_path: Path) -> None:
    seen = steps(tmp_path, {"args": ["x"]}, {"call": "add", "args": [1]}, target="proj:refuse")
    assert len(seen) == 1
    assert seen[0]["raised"]["qualified"] == "builtins.TypeError"


def test_a_value_that_json_cannot_hold_is_observed_with_its_repr(tmp_path: Path) -> None:
    seen = steps(tmp_path, {"args": [4]})
    assert seen == [{"not_json": {"type": "Counter", "repr": "Counter(4)"}}]


def test_a_long_repr_is_observed_cut_one_character_past_the_limit(tmp_path: Path) -> None:
    (seen,) = steps(tmp_path, {}, target="proj:Long")
    assert seen["not_json"]["repr"] == "x" * 1001


def test_a_repr_that_raises_is_observed_without_a_repr(tmp_path: Path) -> None:
    assert steps(tmp_path, {}, target="proj:Broken") == [{"not_json": {"type": "Broken"}}]
