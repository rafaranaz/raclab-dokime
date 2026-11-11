# SDD-EARS: CONTRACT-063 CONTRACT-064 CONTRACT-067 CONTRACT-068 CONTRACT-069
import pytest

from dokime.contract.expectations import AnyValue, Approx, Contains, FullMatch, Json, holds


def test_contains_holds_for_a_text_that_contains_its_text() -> None:
    assert holds(Contains("| foo|bar "), "+---+\n| foo|bar     |\n+---+")
    assert holds(Contains(""), "anything")


@pytest.mark.parametrize("observed", ["| foo\\|bar |", "", 5, None, ["| foo|bar "]])
def test_contains_does_not_hold_without_its_text_or_for_what_is_not_a_text(
    observed: object,
) -> None:
    assert not holds(Contains("| foo|bar "), observed)


def test_fullmatch_holds_when_the_expression_matches_the_whole_text() -> None:
    assert holds(FullMatch(r"\d+ items"), "12 items")
    assert holds(FullMatch(r"(?s)first.*last"), "first\nmiddle\nlast")


@pytest.mark.parametrize("observed", ["total: 12 items", "12 items left", "12 items\n", 12, None])
def test_fullmatch_does_not_hold_for_a_part_of_the_text_or_for_what_is_not_a_text(
    observed: object,
) -> None:
    assert not holds(FullMatch(r"\d+ items"), observed)


@pytest.mark.parametrize(
    "observed",
    ["123e4567-e89b-12d3-a456-426614174000", "123E4567-E89B-12D3-A456-426614174000"],
)
def test_any_uuid_holds_for_a_uuid(observed: str) -> None:
    assert holds(AnyValue("uuid"), observed)


@pytest.mark.parametrize(
    "observed",
    ["123e4567e89b12d3a456426614174000", "123e4567-e89b-12d3-a456-42661417400", "not-a-uuid", 7],
)
def test_any_uuid_does_not_hold_for_another_text_or_kind(observed: object) -> None:
    assert not holds(AnyValue("uuid"), observed)


@pytest.mark.parametrize(
    "observed",
    ["2026-11-10T15:40:02Z", "2026-11-10T15:40:02+01:00", "2026-11-10T15:40:02.123456"],
)
def test_any_timestamp_holds_for_a_date_and_a_time_in_iso_8601(observed: str) -> None:
    assert holds(AnyValue("timestamp"), observed)


@pytest.mark.parametrize(
    "observed",
    ["2026-11-10", "15:40:02", "2026-13-40T15:40:02Z", "10/11/2026 15:40", "yesterday", 1762789202],
)
def test_any_timestamp_does_not_hold_for_another_text_or_kind(observed: object) -> None:
    assert not holds(AnyValue("timestamp"), observed)


def test_json_holds_for_a_text_that_is_json_whose_value_satisfies_what_is_inside() -> None:
    expected = Json({"total": Approx(10.03, 0.005), "lines": 2})
    assert holds(expected, '{"lines": 2, "total": 10.03}\n')
    assert not holds(expected, '{"lines": 3, "total": 10.03}')


@pytest.mark.parametrize("observed", ["{not json", "", 5, {"lines": 2}])
def test_json_does_not_hold_for_what_is_not_a_json_text(observed: object) -> None:
    assert not holds(Json({"lines": 2}), observed)
