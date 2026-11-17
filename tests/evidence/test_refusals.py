# SDD-EARS: EVIDENCE-005 EVIDENCE-044 EVIDENCE-045
from dataclasses import replace

import pytest

from dokime.core.verdicts import Verdict
from dokime.evidence.run import Checks, GateRan, Requirement
from dokime.evidence.statement import build
from tests.evidence.runs import CONTRACT, GATES, run


@pytest.mark.parametrize("story", ["", "1-story", "a/b", "../x", "a--b", "a b", "story-"])
def test_a_story_that_is_not_a_name_is_refused(story: str) -> None:
    with pytest.raises(ValueError, match="story") as raised:
        build(run(story=story))
    assert repr(story) in str(raised.value)


def test_a_requirement_that_is_not_a_name_is_refused() -> None:
    contract = replace(CONTRACT, requirements=(Requirement("R 1", ()),))
    with pytest.raises(ValueError, match="'R 1'"):
        build(run(contract=contract))


def test_an_unstable_example_that_is_not_a_name_is_refused() -> None:
    gate = GateRan("baseline", Verdict.ASK, unstable_examples=("**E**",))
    with pytest.raises(ValueError, match=r"'\*\*E\*\*'"):
        build(run(gates=(gate,)))


def test_two_gates_of_the_same_name_are_refused() -> None:
    with pytest.raises(ValueError, match="'baseline'"):
        build(run(gates=(*GATES, GateRan("baseline", Verdict.PASS))))


@pytest.mark.parametrize("checks", [Checks("sealed", 1), Checks("human", 0)])
def test_a_check_out_of_the_rule_is_refused(checks: Checks) -> None:
    gate = GateRan("visible-examples", Verdict.PASS, checks=(checks,))
    with pytest.raises(ValueError, match="check") as raised:
        build(run(gates=(gate,)))
    assert repr(checks.origin) in str(raised.value)
