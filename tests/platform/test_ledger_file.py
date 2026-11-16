# SDD-EARS: PLATFORM-060 PLATFORM-061 PLATFORM-062 PLATFORM-063
from pathlib import Path

from dokime.core.ledger import Ledger, verify
from dokime.platform.clock import SystemClock
from dokime.platform.ledger_file import LedgerFile


def test_an_appended_line_ends_the_file_with_a_newline(tmp_path: Path) -> None:
    store = LedgerFile(tmp_path / "ledger.jsonl")
    store.append('{"a":1}')
    store.append('{"b":2}')
    assert (tmp_path / "ledger.jsonl").read_bytes() == b'{"a":1}\n{"b":2}\n'


def test_the_lines_come_back_in_order_without_their_newlines(tmp_path: Path) -> None:
    store = LedgerFile(tmp_path / "ledger.jsonl")
    for line in ('{"a":1}', '{"b":"é"}', "{}"):
        store.append(line)
    assert LedgerFile(tmp_path / "ledger.jsonl").lines() == ('{"a":1}', '{"b":"é"}', "{}")


def test_a_store_whose_file_does_not_exist_gives_no_lines(tmp_path: Path) -> None:
    assert LedgerFile(tmp_path / "absent.jsonl").lines() == ()
    assert not (tmp_path / "absent.jsonl").exists()


def test_the_first_append_creates_the_file(tmp_path: Path) -> None:
    store = LedgerFile(tmp_path / "ledger.jsonl")
    store.append("{}")
    assert (tmp_path / "ledger.jsonl").is_file()


def test_a_ledger_written_through_the_file_verifies_and_continues(tmp_path: Path) -> None:
    path = tmp_path / "ledger.jsonl"
    Ledger(LedgerFile(path), SystemClock()).record("run.started", {"note": "é"})
    Ledger(LedgerFile(path), SystemClock()).record("run.finished", {})
    assert verify(LedgerFile(path).lines()) == ()
    assert len(LedgerFile(path).lines()) == 2


def test_an_empty_file_gives_no_lines(tmp_path: Path) -> None:
    (tmp_path / "ledger.jsonl").write_bytes(b"")
    assert LedgerFile(tmp_path / "ledger.jsonl").lines() == ()


def test_a_cut_last_line_is_given_so_that_the_verification_reports_it(tmp_path: Path) -> None:
    (tmp_path / "ledger.jsonl").write_bytes(b'{"a":1}\n{"b":')
    lines = LedgerFile(tmp_path / "ledger.jsonl").lines()
    assert lines == ('{"a":1}', '{"b":')
    assert [finding.code for finding in verify(lines)][-1] == "not-an-event"
