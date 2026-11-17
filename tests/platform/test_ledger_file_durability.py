# SDD-EARS: PLATFORM-067 PLATFORM-068
"""What the store asks of the system, seen by replacing `os.write` and `os.fsync`.

A partial write and a crash cannot be made to happen in a test, so these tests watch the calls.
"""

import os
from pathlib import Path

import pytest

from dokime.platform.ledger_file import LedgerFile


def test_a_partial_write_is_completed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    write = os.write

    def three_bytes_at_a_time(descriptor: int, data: bytes) -> int:
        return write(descriptor, bytes(data[:3]))

    monkeypatch.setattr(os, "write", three_bytes_at_a_time)
    LedgerFile(tmp_path / "ledger.jsonl").append('{"a":"bcdefgh"}')
    assert (tmp_path / "ledger.jsonl").read_bytes() == b'{"a":"bcdefgh"}\n'


def test_a_write_that_writes_nothing_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(os, "write", lambda descriptor, data: 0)
    with pytest.raises(OSError, match="wrote nothing"):
        LedgerFile(tmp_path / "ledger.jsonl").append("{}")


def flushed(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    seen: list[str] = []
    fsync = os.fsync

    def watched(descriptor: int) -> None:
        seen.append(os.readlink(f"/proc/self/fd/{descriptor}"))
        fsync(descriptor)

    monkeypatch.setattr(os, "fsync", watched)
    return seen


def test_creating_the_file_flushes_its_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    seen = flushed(monkeypatch)
    LedgerFile(tmp_path / "ledger.jsonl").append("{}")
    assert str(tmp_path) in seen
    assert str(tmp_path / "ledger.jsonl") in seen


def test_appending_to_a_file_that_exists_does_not_flush_its_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    LedgerFile(tmp_path / "ledger.jsonl").append("{}")
    seen = flushed(monkeypatch)
    LedgerFile(tmp_path / "ledger.jsonl").append("{}")
    assert seen == [str(tmp_path / "ledger.jsonl")]
