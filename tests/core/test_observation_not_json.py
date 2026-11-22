# SDD-EARS: CORE-191 CORE-192 CORE-193
import pytest

from dokime.core.observation import REPR_LIMIT, NotJson, not_json


def test_a_value_json_cannot_hold_keeps_its_whole_repr_within_the_limit() -> None:
    for text in ("{1, 2}", "x" * REPR_LIMIT):
        seen = not_json("set", text)
        assert (seen.type, seen.representation, seen.cut) == ("set", text, False)


def test_a_repr_over_the_limit_keeps_its_first_characters_and_a_mark() -> None:
    seen = not_json("Version", "v" * (REPR_LIMIT + 1))
    assert seen.representation == "v" * REPR_LIMIT
    assert seen.cut


def test_the_limit_is_a_thousand_characters() -> None:
    assert REPR_LIMIT == 1000


@pytest.mark.parametrize(
    ("representation", "cut"),
    [("x" * (REPR_LIMIT + 1), False), ("x" * (REPR_LIMIT + 1), True), ("short", True)],
)
def test_an_observation_that_breaks_the_limit_is_rejected(representation: str, cut: bool) -> None:
    with pytest.raises(ValueError, match="representation"):
        NotJson(type="set", representation=representation, cut=cut)
