# SDD-EARS: CONTRACT-065 CONTRACT-066
import pytest

from dokime.contract.expectations import Approx, Contains, Unordered, holds


@pytest.mark.parametrize("observed", [10.03, 10.035, 10.025, 10.0299])
def test_approx_holds_for_a_number_within_the_tolerance(observed: float) -> None:
    assert holds(Approx(10.03, 0.0051), observed)


def test_approx_holds_for_an_integer_within_the_tolerance() -> None:
    assert holds(Approx(10.0, 0.5), 10)


@pytest.mark.parametrize("observed", [10.04, 10.02, "10.03", True, None, [10.03]])
def test_approx_does_not_hold_outside_the_tolerance_or_for_what_is_not_a_number(
    observed: object,
) -> None:
    assert not holds(Approx(10.03, 0.005), observed)


def test_unordered_holds_for_the_same_items_in_any_order() -> None:
    assert holds(Unordered((1, "a", {"k": 2})), [{"k": 2}, 1, "a"])
    assert holds(Unordered(()), [])


def test_unordered_pairs_each_item_with_a_different_observed_item() -> None:
    expected = Unordered((Contains("a"), Contains("ab")))
    assert holds(expected, ["ab", "a"])
    assert holds(expected, ["a", "ab"])
    assert not holds(expected, ["a", "a"])


@pytest.mark.parametrize("observed", [[1, 2], [1, 2, 2, 3], [1, 2, 4], [1, 1, 2], "123", None])
def test_unordered_does_not_hold_for_other_items_or_for_what_is_not_a_list(
    observed: object,
) -> None:
    assert not holds(Unordered((1, 2, 3)), observed)
