# SDD-EARS: CORE-135 CORE-136 CORE-137 CORE-138 CORE-139 CORE-140 CORE-145 CORE-146
import json
from collections.abc import Callable

import pytest

from dokime.core.canonical import canonical
from dokime.core.clock import Clock
from dokime.core.ledger import LedgerStore, verify
from tests.core.ledgers import THREE, found, parsed, rehashed, written


def test_a_ledger_written_by_the_ledger_verifies() -> None:
    assert verify(written(*THREE).kept) == ()
    assert verify([]) == ()


@pytest.mark.parametrize(
    "line",
    [
        "not json",
        "[1, 2]",
        '{"seq": 1}',
        canonical({"seq": "1", "at": "", "type": "run.started", "prev": None, "hash": ""}),
    ],
    ids=["not-json", "a-list", "missing-fields", "seq-as-text"],
)
def test_a_line_that_is_not_an_event_is_found(line: str) -> None:
    store = written(*THREE)
    assert found([store.kept[0], line, *store.kept[1:]])[0] == ("not-an-event", (2,))


def test_an_event_of_a_type_outside_the_table_is_not_an_event() -> None:
    first = parsed(written(*THREE))[0]
    first["type"] = "run.paused"
    assert found([rehashed(first)]) == [("not-an-event", (1,))]


@pytest.mark.parametrize(
    "change",
    [
        lambda line: line.replace(":", ": "),
        lambda line: line + " ",
        lambda line: json.dumps(json.loads(line)),
    ],
    ids=["spaces", "a-trailing-space", "another-order"],
)
def test_a_line_that_is_not_the_canonical_form_of_its_event_is_found(
    change: Callable[[str], str],
) -> None:
    store = written(*THREE)
    store.kept[1] = change(store.kept[1])
    assert ("not-canonical", (2,)) in found(store.kept)


def test_an_event_whose_hash_is_not_its_digest_is_found() -> None:
    store = written(*THREE)
    store.kept[2] = store.kept[2].replace("done", "lost")
    assert found(store.kept) == [("wrong-hash", (3,))]


def test_an_event_whose_previous_hash_breaks_the_chain_is_found() -> None:
    events = parsed(written(*THREE))
    events[1]["prev"] = "sha256:" + "0" * 64
    lines = [rehashed(event) for event in events]
    assert found(lines) == [("broken-chain", (2,)), ("broken-chain", (3,))]


def test_a_first_event_with_a_previous_hash_is_found() -> None:
    events = parsed(written(*THREE))
    events[0]["prev"] = "sha256:" + "0" * 64
    assert ("broken-chain", (1,)) in found([rehashed(events[0])])


@pytest.mark.parametrize(("first", "second"), [(1, 3), (2, 3), (1, 1)])
def test_an_event_out_of_sequence_is_found(first: int, second: int) -> None:
    events = parsed(written(*THREE[:2]))
    events[0]["seq"], events[1]["seq"] = first, second
    head = rehashed(events[0])
    events[1]["prev"] = json.loads(head)["hash"]
    codes = found([head, rehashed(events[1])])
    assert ("wrong-sequence", (1,) if first != 1 else (2,)) in codes


def test_every_finding_of_the_verification_fails() -> None:
    store = written(*THREE)
    store.kept[0] = "not json"
    assert {finding.verdict.value for finding in verify(store.kept)} == {"FAIL"}


def test_the_port_of_the_store_offers_append_and_lines() -> None:
    public = {name for name in vars(LedgerStore) if not name.startswith("_")}
    assert public == {"append", "lines"}


def test_the_port_of_the_clock_offers_the_current_time() -> None:
    public = {name for name in vars(Clock) if not name.startswith("_")}
    assert public == {"now"}


def test_an_event_with_a_value_that_has_no_canonical_form_is_found() -> None:
    store = written(*THREE)
    store.kept[1] = store.kept[1].replace('"verdict":"PASS"', '"verdict":0.5')
    assert found(store.kept) == [("not-canonical", (2,)), ("wrong-hash", (2,))]
