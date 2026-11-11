# SDD-EARS: CORE-001 CORE-002 CORE-003 CORE-004 CORE-005 CORE-006 CORE-007
from itertools import permutations, product

import pytest

from dokime.core.verdicts import EmptyRoundError, Verdict, aggregate


def test_the_verdict_type_has_exactly_four_values() -> None:
    assert {verdict.value for verdict in Verdict} == {"PASS", "FAIL", "ASK", "ERROR"}


@pytest.mark.parametrize(
    "others",
    [[], ["PASS"], ["FAIL"], ["ASK"], ["FAIL", "ASK", "PASS"]],
)
def test_any_error_gives_error(others: list[str]) -> None:
    round_ = [Verdict("ERROR"), *(Verdict(other) for other in others)]
    assert aggregate(round_) is Verdict("ERROR")


@pytest.mark.parametrize("others", [[], ["PASS"], ["ASK"], ["ASK", "PASS"]])
def test_a_fail_without_error_gives_fail(others: list[str]) -> None:
    round_ = [Verdict("FAIL"), *(Verdict(other) for other in others)]
    assert aggregate(round_) is Verdict("FAIL")


@pytest.mark.parametrize("others", [[], ["PASS"], ["PASS", "PASS"]])
def test_an_ask_without_error_or_fail_gives_ask(others: list[str]) -> None:
    round_ = [Verdict("ASK"), *(Verdict(other) for other in others)]
    assert aggregate(round_) is Verdict("ASK")


@pytest.mark.parametrize("size", [1, 2, 5])
def test_all_pass_gives_pass(size: int) -> None:
    assert aggregate([Verdict("PASS")] * size) is Verdict("PASS")


def test_an_empty_round_is_an_error_that_says_so() -> None:
    with pytest.raises(EmptyRoundError, match="empty"):
        aggregate([])


def test_the_order_of_the_verdicts_does_not_change_the_result() -> None:
    for round_ in product(list(Verdict), repeat=3):
        results = {aggregate(order) for order in permutations(round_)}
        assert len(results) == 1, round_


def test_a_round_can_be_any_iterable() -> None:
    assert aggregate(verdict for verdict in [Verdict("PASS"), Verdict("ASK")]) is Verdict("ASK")
