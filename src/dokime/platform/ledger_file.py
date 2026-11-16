"""The ledger store over one file of the state directory of the harness.

Each line of the file is one event of the ledger, ended by a newline; the canonical form of an
event keeps it on one line. A line is written with one call in append mode and flushed to the
storage device before `append` returns, so a crash leaves at most the last line cut, which the
store then refuses to append after and the verification of the ledger reports.
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
        descriptor = os.open(
            self.path, os.O_WRONLY | os.O_APPEND | os.O_CREAT | os.O_CLOEXEC, 0o600
        )
        try:
            os.write(descriptor, line.encode("utf-8") + _NEWLINE)
            os.fsync(descriptor)
        finally:
            os.close(descriptor)

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
