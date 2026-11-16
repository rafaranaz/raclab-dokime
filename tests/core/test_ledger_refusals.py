# SDD-EARS: CORE-125 CORE-127 CORE-128 CORE-129 CORE-130 CORE-131
import re
from datetime import datetime

import pytest

from dokime.core.canonical import NotCanonicalError
from dokime.core.ledger import Ledger, LedgerError, verify
from tests.core.ledgers import THREE, Lines, Ticks, parsed, written


def test_a_time_without_a_time_zone_is_refused_and_nothing_is_written() -> None:
    store = Lines()
    with pytest.raises(LedgerError, match="time zone"):
        Ledger(store, Ticks(datetime(2026, 11, 17, 9, 30))).record("run.started", {})
    assert store.kept == []


def test_a_type_outside_the_table_is_refused_naming_it_and_nothing_is_written() -> None:
    store = Lines()
    with pytest.raises(LedgerError, match=re.escape("gate.skipped")):
        Ledger(store, Ticks()).record("gate.skipped", {})
    assert store.kept == []


@pytest.mark.parametrize("name", ["seq", "at", "type", "prev", "hash"])
def test_a_field_named_as_one_of_the_ledger_is_refused_naming_it(name: str) -> None:
    store = Lines()
    with pytest.raises(LedgerError, match=name):
        Ledger(store, Ticks()).record("run.started", {name: 1})
    assert store.kept == []


def test_fields_without_a_canonical_form_are_refused_with_its_error() -> None:
    store = Lines()
    with pytest.raises(NotCanonicalError, match="ratio"):
        Ledger(store, Ticks()).record("gate.finished", {"ratio": 0.5})
    assert store.kept == []


def test_a_ledger_opened_on_a_store_with_events_continues_their_chain() -> None:
    store = written(*THREE[:2])
    last = parsed(store)[-1]
    Ledger(store, Ticks()).record("run.finished", {"state": "done"})
    third = parsed(store)[-1]
    assert (third["seq"], third["prev"]) == (3, last["hash"])
    assert verify(store.kept) == ()


def test_a_ledger_opened_on_a_store_that_does_not_verify_is_refused() -> None:
    store = written(*THREE)
    store.kept[1] = store.kept[1].replace("PASS", "FAIL")
    with pytest.raises(LedgerError, match="wrong-hash"):
        Ledger(store, Ticks())
