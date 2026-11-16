# SDD-EARS: CORE-141 CORE-142 CORE-143 CORE-144
import json

import pytest

from dokime.core.ledger import Head, LedgerError, head, verify
from tests.core.ledgers import THREE, written


def test_the_head_is_the_hash_of_the_last_event_and_the_number_of_events() -> None:
    lines = written(*THREE).kept
    assert head(lines) == Head(hash=json.loads(lines[-1])["hash"], events=3)


def test_the_head_of_a_ledger_without_events_has_no_hash_and_no_events() -> None:
    assert head([]) == Head(hash=None, events=0)


def test_the_head_of_a_ledger_that_does_not_verify_is_refused() -> None:
    lines = written(*THREE).kept
    lines[0] = lines[0].replace("run.started", "run.paused")
    with pytest.raises(LedgerError, match="line 1"):
        head(lines)


def test_a_ledger_verified_against_its_own_head_gives_no_finding() -> None:
    lines = written(*THREE).kept
    assert verify(lines, head(lines)) == ()


def test_a_ledger_whose_last_events_were_removed_is_found_by_its_head() -> None:
    lines = written(*THREE).kept
    expected = head(lines)
    shorter = lines[:2]
    assert verify(shorter) == ()
    (finding,) = verify(shorter, expected)
    assert (finding.code, str(expected.events) in finding.message) == ("wrong-head", True)


def test_a_ledger_written_again_from_the_start_is_found_by_its_head() -> None:
    expected = head(written(*THREE).kept)
    again = written(*THREE[:2], ("run.finished", {"state": "rewritten"})).kept
    assert verify(again) == ()
    assert [finding.code for finding in verify(again, expected)] == ["wrong-head"]


def test_the_finding_of_a_wrong_head_gives_both_heads() -> None:
    lines = written(*THREE).kept
    expected = Head(hash="sha256:" + "0" * 64, events=3)
    (finding,) = verify(lines, expected)
    assert "sha256:" + "0" * 64 in finding.message
    assert json.loads(lines[-1])["hash"] in finding.message
