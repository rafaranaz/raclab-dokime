# SDD-EARS: CONTRACT-060 CONTRACT-061 CONTRACT-062
import pytest

from dokime.contract.expectations import Approx, Contains, Expected, holds, is_exact


@pytest.mark.parametrize("value", [None, True, False, 0, 7, -3, 1.5, "", "text", [], {}])
def test_an_exact_value_holds_for_an_equal_value_of_the_same_type(value: Expected) -> None:
    assert holds(value, value)


@pytest.mark.parametrize(
    ("expected", "observed"),
    [
        (1, 1.0),
        (1.0, 1),
        (1, True),
        (True, 1),
        (0, False),
        (0, None),
        ("1", 1),
        (1, "1"),
        ("a", "b"),
        (1, 2),
        (None, ""),
        ("", None),
        ([], {}),
        ({}, []),
    ],
)
def test_an_exact_value_does_not_hold_for_another_type_or_another_value(
    expected: Expected, observed: object
) -> None:
    assert not holds(expected, observed)


def test_a_mapping_holds_for_a_mapping_with_the_same_keys_whose_values_hold() -> None:
    expected: Expected = {"total": Approx(10.03, 0.005), "currency": "EUR"}
    assert holds(expected, {"currency": "EUR", "total": 10.031})
    assert not holds(expected, {"currency": "EUR", "total": 10.2})


@pytest.mark.parametrize(
    "observed",
    [{"a": 1}, {"a": 1, "b": 2, "c": 3}, {"a": 1, "c": 2}, [1, 2], "a", None],
)
def test_a_mapping_does_not_hold_for_other_keys_or_for_what_is_not_a_mapping(
    observed: object,
) -> None:
    assert not holds({"a": 1, "b": 2}, observed)


def test_a_list_holds_for_a_list_of_the_same_length_whose_items_hold_in_order() -> None:
    expected: Expected = ["a", Contains("b"), 3]
    assert holds(expected, ["a", "abc", 3])
    assert not holds(expected, ["abc", "a", 3])


@pytest.mark.parametrize("observed", [[1], [1, 2, 3], [2, 1], (1, 2), "12", None])
def test_a_list_does_not_hold_for_another_length_order_or_kind(observed: object) -> None:
    assert not holds([1, 2], observed)


def test_an_expectation_is_exact_when_it_has_no_matcher_inside() -> None:
    assert is_exact({"a": [1, "x", None], "b": {"c": 2.5}})
    assert not is_exact({"a": [1, Contains("x")]})
    assert not is_exact(Approx(1.0, 0.1))
