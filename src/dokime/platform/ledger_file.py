"""The ledger store over one file of the state directory of the harness.

Each line of the file is one event of the ledger, ended by a newline; the canonical form of an event
keeps it on one line. A line is written in append mode until every byte of it is written, and
flushed to the storage device before `append` returns, with the directory when the file is new, so a
crash leaves at most the last line cut, which the store then refuses to append after and the
verification of the ledger reports.
"""

import os
from pathlib import Path

_NEWLINE = b"\n"


class LedgerFile:
    """Keeps the lines of a ledger in a file, one event per line."""

    def __init__(self, path: Path) -> None:
        self.path = path

    def append(self, line: str) -> None:
        """Append one line, refusing one that would not stay one line or a file that was cut."""
        if "\n" in line or "\r" in line:
            raise ValueError("a line of the ledger is one line: it holds no newline")
        if self._cut():
            raise ValueError(
                f"the last line of {self.path} is cut, so nothing is appended after it"
            )
        created = not self.path.exists()
        flags = os.O_WRONLY | os.O_APPEND | os.O_CREAT | os.O_CLOEXEC
        descriptor = os.open(self.path, flags, 0o600)
        try:
            _write_all(descriptor, line.encode("utf-8") + _NEWLINE)
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        if created:
            _flush_directory(self.path.parent)

    def lines(self) -> tuple[str, ...]:
        """The lines, in the order they were appended, without their newlines."""
        if not self.path.exists():
            return ()
        try:
            text = self.path.read_bytes().decode("utf-8")
        except UnicodeDecodeError:
            raise ValueError(f"the ledger {self.path} is not valid UTF-8") from None
        if not text:
            return ()
        lines = text.split("\n")
        if text.endswith("\n"):
            lines.pop()
        return tuple(lines)

    def _cut(self) -> bool:
        if not self.path.exists() or self.path.stat().st_size == 0:
            return False
        with self.path.open("rb") as handle:
            handle.seek(-1, os.SEEK_END)
            return handle.read(1) != _NEWLINE


def _write_all(descriptor: int, data: bytes) -> None:
    """Write every byte: the system may write fewer than it is given, as on a full disk."""
    view = memoryview(data)
    while view:
        written = os.write(descriptor, view)
        if written == 0:
            raise OSError(f"the system wrote nothing of the {len(view)} bytes left of the line")
        view = view[written:]


def _flush_directory(directory: Path) -> None:
    """Flush the entry of a new file, so that a crash right after does not lose it."""
    descriptor = os.open(directory, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
