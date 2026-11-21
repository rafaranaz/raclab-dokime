# SDD-EARS: ORACLE-052 ORACLE-053 ORACLE-054
from math import factorial

import pytest

from dokime.oracle.relations import orders


def inputs(items: list[object], found: tuple[tuple[int, ...], ...]) -> list[tuple[object, ...]]:
    return [tuple(items[i] for i in order) for order in found]


def test_the_reversed_order_comes_first_and_then_the_drawn_ones() -> None:
    items = ["a", "b", "c", "d"]
    found = orders(items, seed=7, permutations=5)
    assert found[0] == (3, 2, 1, 0)
    assert len(found) == 6
    assert all(sorted(order) == [0, 1, 2, 3] for order in found)


def test_the_same_seed_gives_the_same_orders_in_the_same_order() -> None:
    items = list(range(8))
    first = orders(items, seed=20261121, permutations=10)
    assert first == orders(items, seed=20261121, permutations=10)
    assert first == orders(list(items), seed=20261121, permutations=10)
    assert first != orders(items, seed=20261122, permutations=10)
    assert first[:1] == ((7, 6, 5, 4, 3, 2, 1, 0),)
    assert len(first) == 11


def test_the_orders_of_a_seed_are_pinned_whether_drawn_from_all_or_by_shuffling() -> None:
    assert orders(["a", "b", "c", "d"], seed=7, permutations=3) == (
        (3, 2, 1, 0),
        (1, 3, 2, 0),
        (0, 3, 2, 1),
        (2, 0, 3, 1),
    )
    assert orders(list(range(8)), seed=20261121, permutations=3) == (
        (7, 6, 5, 4, 3, 2, 1, 0),
        (5, 3, 1, 0, 4, 6, 7, 2),
        (5, 3, 7, 4, 2, 6, 1, 0),
        (4, 1, 6, 0, 7, 2, 3, 5),
    )


def test_the_orders_depend_on_the_items_only_through_which_are_equal() -> None:
    assert orders(["a", "b", "c"], seed=1, permutations=10) == orders(
        ["x", "y", "z"], seed=1, permutations=10
    )


@pytest.mark.parametrize("seed", range(20))
def test_repeated_items_never_give_the_source_nor_two_equal_inputs(seed: int) -> None:
    items: list[object] = ["a", "a", "b", "b", "c"]
    found = orders(items, seed=seed, permutations=100)
    given = inputs(items, found)
    assert tuple(items) not in given
    assert len(set(given)) == len(given)
    distinct = factorial(5) // (factorial(2) * factorial(2))
    assert len(given) == distinct - 1


def test_the_reversed_order_equal_to_the_source_is_not_given() -> None:
    items: list[object] = ["a", "b", "a"]
    given = inputs(items, orders(items, seed=3, permutations=10))
    assert ("a", "b", "a") not in given
    assert sorted(given) == [("a", "a", "b"), ("b", "a", "a")]


@pytest.mark.parametrize("items", [[], ["a"], ["a", "a"], ["x", "x", "x", "x"]])
def test_items_that_allow_no_other_input_give_no_order(items: list[object]) -> None:
    assert orders(items, seed=1, permutations=10) == ()


def test_the_number_bounds_the_drawn_orders_besides_the_reversed_one() -> None:
    items = list(range(6))
    assert len(orders(items, seed=5, permutations=1)) == 2
    assert len(orders(items, seed=5, permutations=10)) == 11


def test_unhashable_items_are_compared_by_their_value() -> None:
    items: list[object] = [{"a": 1}, {"a": 1}, [2]]
    given = inputs(items, orders(items, seed=2, permutations=10))
    assert len(given) == 2
    assert tuple(items) not in given
