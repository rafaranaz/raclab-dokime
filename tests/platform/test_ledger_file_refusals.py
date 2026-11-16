# SDD-EARS: PLATFORM-064 PLATFORM-065 PLATFORM-066
import re
from pathlib import Path

import pytest

from dokime.platform.ledger_file import LedgerFile


@pytest.mark.parametrize("line", ["a\nb", "a\rb", "a\n"])
def test_a_line_that_would_break_the_file_is_refused_and_nothing_written(
    tmp_path: Path, line: str
) -> None:
    store = LedgerFile(tmp_path / "ledger.jsonl")
    store.append("{}")
    with pytest.raises(ValueError, match="one line"):
        store.append(line)
    assert store.lines() == ("{}",)


def test_a_file_whose_last_line_was_cut_refuses_to_append(tmp_path: Path) -> None:
    (tmp_path / "ledger.jsonl").write_bytes(b'{"a":1}\n{"b":')
    with pytest.raises(ValueError, match="cut"):
        LedgerFile(tmp_path / "ledger.jsonl").append("{}")
    assert (tmp_path / "ledger.jsonl").read_bytes() == b'{"a":1}\n{"b":'


def test_a_file_that_is_not_utf_8_refuses_to_give_its_lines(tmp_path: Path) -> None:
    (tmp_path / "ledger.jsonl").write_bytes(b"\xff\n")
    with pytest.raises(ValueError, match=re.escape("ledger.jsonl")):
        LedgerFile(tmp_path / "ledger.jsonl").lines()
