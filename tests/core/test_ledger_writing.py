# SDD-EARS: CORE-120 CORE-121 CORE-122 CORE-123 CORE-124 CORE-126
import json
from datetime import datetime, timedelta, timezone

from dokime.core.canonical import canonical, digest
from dokime.core.ledger import TYPES, Ledger
from tests.core.ledgers import THREE, Lines, Ticks, parsed, written


def test_the_events_are_numbered_from_one() -> None:
    assert [event["seq"] for event in parsed(written(*THREE))] == [1, 2, 3]


def test_the_first_event_has_no_previous_hash() -> None:
    assert parsed(written(*THREE))[0]["prev"] is None


def test_each_later_event_carries_the_hash_of_the_one_before() -> None:
    events = parsed(written(*THREE))
    assert [event["prev"] for event in events[1:]] == [event["hash"] for event in events[:-1]]


def test_the_hash_of_an_event_is_the_digest_of_the_event_without_it() -> None:
    for event in parsed(written(*THREE)):
        given = event.pop("hash")
        assert given == digest(event)


def test_an_event_is_stamped_with_the_time_of_the_clock_in_utc_to_the_second() -> None:
    store = Lines()
    two_hours_east = timezone(timedelta(hours=2))
    clock = Ticks(datetime(2026, 11, 17, 11, 30, 5, 900, tzinfo=two_hours_east))
    Ledger(store, clock).record("run.started", {})
    assert parsed(store)[0]["at"] == "2026-11-17T09:30:05Z"


def test_each_event_is_one_line_that_is_its_canonical_form() -> None:
    store = written(*THREE)
    assert len(store.kept) == 3
    for line in store.kept:
        assert "\n" not in line
        assert line == canonical(json.loads(line))


def test_the_fields_of_its_type_are_kept_beside_those_of_the_ledger() -> None:
    first = parsed(written(*THREE))[0]
    assert first["type"] == "run.started"
    assert first["inputs"] == {"contract": "sha256:" + "a" * 64}


def test_the_table_of_types_is_that_of_the_architecture() -> None:
    assert len(TYPES) == 13
