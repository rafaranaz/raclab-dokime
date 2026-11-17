# SDD-EARS: VERIFY-003 VERIFY-004
import pytest

from dokime.verify.result import Checks, GateResult, checks_of


def test_the_checks_are_counted_by_origin_in_their_order() -> None:
    counted = checks_of(["model", "human", "existing", "human"])
    assert counted == (Checks("existing", 1), Checks("human", 2), Checks("model", 1))


def test_no_checks_give_no_entry() -> None:
    assert checks_of([]) == ()
    assert GateResult(gate="g", findings=()).checks == ()


def test_a_result_carries_its_checks() -> None:
    given = (Checks("human", 3), Checks("derived", 1))
    assert GateResult(gate="g", findings=(), checks=given).checks == given


@pytest.mark.parametrize(
    "given",
    [
        (Checks("sealed", 1),),
        (Checks("human", 1), Checks("human", 2)),
        (Checks("model", 1), Checks("human", 1)),
        (Checks("human", 0),),
    ],
)
def test_checks_out_of_the_rule_are_refused(given: tuple[Checks, ...]) -> None:
    with pytest.raises(ValueError, match="checks"):
        GateResult(gate="g", findings=(), checks=given)
