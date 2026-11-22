# SDD-EARS: VERIFY-164 VERIFY-188 VERIFY-189 VERIFY-190
import dataclasses

import pytest

from dokime.contract.expectations import Repr
from dokime.contract.model import Example, Step
from dokime.core.verdicts import Verdict
from tests.verify.gates import codes, contract, example, on_base, on_change
from tests.verify.sealed_contracts import batch_of, held, run, split

TEXT = "Version(major=1, minor=0, patch=0, prerelease=None, build=None)"
NOT_RECORDED = {"not_json": "Version"}
RECORDED = {"not_json": "Version", "repr": TEXT}


def by_repr(name: str, requirement: str, origin: str = "human") -> Example:
    step = Step(input={"args": [1]}, expect={"returns": Repr(TEXT)})
    return dataclasses.replace(example(name, requirement, origin), steps=(step,))


@pytest.mark.parametrize("requirement", ["R-new", "R-keep", "R-change"])
def test_a_comparison_on_the_base_that_is_not_recorded_is_an_error_and_nothing_else(
    requirement: str,
) -> None:
    findings, _ = on_base(contract(by_repr("E-1", requirement)), {"E-1": NOT_RECORDED})  # type: ignore[dict-item]
    assert codes(findings) == [("repr-not-recorded", Verdict.ERROR)]
    assert "E-1" in findings[0].message


def test_runs_on_the_base_of_which_one_is_not_recorded_are_an_error_not_a_variation() -> None:
    runs = [{"E-1": RECORDED}, {"E-1": NOT_RECORDED}]
    findings, _ = on_base(contract(by_repr("E-1", "R-keep")), runs, runs=2)  # type: ignore[arg-type]
    assert codes(findings) == [("repr-not-recorded", Verdict.ERROR)]


def test_a_repr_recorded_on_the_base_is_judged_as_before() -> None:
    findings, _ = on_base(contract(by_repr("E-1", "R-keep")), {"E-1": RECORDED})  # type: ignore[dict-item]
    assert findings == []


@pytest.mark.parametrize("origin", ["human", "model", "derived"])
def test_a_comparison_on_the_change_that_is_not_recorded_is_an_error(origin: str) -> None:
    findings, _ = on_change(contract(by_repr("E-1", "R-new", origin)), {"E-1": NOT_RECORDED})  # type: ignore[dict-item]
    assert codes(findings) == [("repr-not-recorded", Verdict.ERROR)]


def held_by_repr(name: str) -> str:
    return held(name).replace("{returns: 2}", f"{{returns: {{$repr: '{TEXT}'}}}}")


def test_a_held_out_comparison_that_is_not_recorded_is_an_error_without_a_value() -> None:
    contract_, sealed = split(("E-h1", held_by_repr("E-h1")), ("E-h2", held_by_repr("E-h2")))
    answers = {"E-h1": NOT_RECORDED, "E-h2": RECORDED, "E-cana": RECORDED}
    result, _ = run(contract_, batch_of(contract_, sealed), answers)  # type: ignore[arg-type]
    (found,) = result.findings
    assert codes([found]) == [("repr-not-recorded", Verdict.ERROR)]
    assert "R-new" in found.message
    for leak in ("E-h1", "E-h2", "E-cana", "Version(", "args"):
        assert leak not in found.message, leak


def test_a_canary_whose_repr_was_not_recorded_does_not_hold_and_is_recorded() -> None:
    # The canary expects a text of 32 hexadecimal digits (VERIFY-151), never a $repr, so its
    # comparison is always recorded and a repr that was not recorded cannot make it pass; if the
    # canary could ever expect a $repr, the gate would need a rule for a canary not recorded.
    contract_, sealed = split(("E-h1", held_by_repr("E-h1")), ("E-h2", held_by_repr("E-h2")))
    answers = {"E-h1": RECORDED, "E-h2": RECORDED, "E-cana": NOT_RECORDED}
    result, _ = run(contract_, batch_of(contract_, sealed), answers)  # type: ignore[arg-type]
    assert result.findings == ()
