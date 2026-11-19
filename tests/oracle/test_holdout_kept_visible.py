# SDD-EARS: ORACLE-045 ORACLE-046 ORACLE-047
import random

import pytest

from dokime.oracle.holdout import split
from tests.oracle.test_holdout import CONTRACT, ids


@pytest.mark.parametrize("seed", [0, 1, 7, 20261119])
def test_an_example_kept_visible_is_never_held_out(seed: int) -> None:
    done = split(CONTRACT, seed, keep_visible={"E-01", "E-02"})
    assert "E-01" not in ids(done.held_out)
    assert "E-02" not in ids(done.held_out)
    assert {"E-01", "E-02"} <= set(ids(done.visible))


def test_the_draw_is_among_the_other_examples_of_the_case() -> None:
    chance = random.Random(5)  # noqa: S311 - a draw anyone can repeat
    expected = {chance.choice(["E-03", "E-05"]), chance.choice(["E-06"])}
    assert set(ids(split(CONTRACT, 5, keep_visible={"E-01", "E-02"}).held_out)) == expected


def test_a_case_where_every_example_is_kept_visible_holds_out_none() -> None:
    done = split(CONTRACT, 3, keep_visible={"E-02", "E-06"})
    assert [e.case for e in done.held_out if e.requirement == "a"] == ["one"]
    assert ("a", "two") in done.cases_without_holdout


def test_the_cases_without_a_held_out_example_are_named_in_order() -> None:
    assert split(CONTRACT, 3).cases_without_holdout == (("b", "one"), ("c", "solo"))
    assert split(CONTRACT, 3, keep_visible={"E-02", "E-06"}).cases_without_holdout == (
        ("a", "two"),
        ("b", "one"),
        ("c", "solo"),
    )


def test_an_example_to_keep_visible_that_the_contract_does_not_have_is_refused() -> None:
    with pytest.raises(ValueError, match="E-99"):
        split(CONTRACT, 3, keep_visible={"E-01", "E-99"})
