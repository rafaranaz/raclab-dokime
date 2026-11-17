# SDD-EARS: ORACLE-010 ORACLE-011 ORACLE-012
from dokime.contract.expectations import Approx
from dokime.core.observation import NotJson, Returned
from dokime.oracle.compare import compare
from tests.oracle.examples import example, observed, raised


def test_a_returned_value_holds_by_the_rules_of_the_contract() -> None:
    assert compare(
        example("function", {"returns": Approx(1.0, 0.1)}), observed(Returned(1.05))
    ).holds
    assert not compare(example("function", {"returns": 1}), observed(Returned(1.0))).holds
    assert not compare(example("function", {"returns": 1}), observed(Returned(True))).holds


def test_a_step_that_raised_where_a_value_was_expected_says_so() -> None:
    comparison = compare(
        example("function", {"returns": 1}), observed(raised("builtins", "TypeError"))
    )
    (difference,) = comparison.differences
    assert (difference.part, "raised builtins.TypeError" in str(difference.observed)) == (
        "returns",
        True,
    )


def test_a_step_that_returned_what_json_cannot_hold_says_so() -> None:
    (difference,) = compare(
        example("function", {"returns": [1]}), observed(NotJson("set"))
    ).differences
    assert "set" in str(difference.observed)


def test_a_step_that_returned_where_an_exception_was_expected_says_what() -> None:
    comparison = compare(
        example("function", {"raises": {"type": "TypeError"}}), observed(Returned("1.2.3"))
    )
    (difference,) = comparison.differences
    assert (difference.part, "1.2.3" in str(difference.observed)) == ("raises", True)
