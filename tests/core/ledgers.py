"""A ledger store in memory, a clock that ticks, and ledgers written with them."""

import json
from collections.abc import Mapping
from datetime import UTC, datetime, timedelta

from dokime.core.canonical import canonical, digest
from dokime.core.ledger import Ledger, verify

START = datetime(2026, 11, 17, 9, 30, 5, 123456, tzinfo=UTC)


class Lines:
    """A ledger store in memory."""

    def __init__(self, lines: tuple[str, ...] = ()) -> None:
        self.kept = list(lines)

    def append(self, line: str) -> None:
        self.kept.append(line)

    def lines(self) -> tuple[str, ...]:
        return tuple(self.kept)


class Ticks:
    """A clock that gives a fixed time and moves one second each time it is asked."""

    def __init__(self, start: datetime = START) -> None:
        self.next = start

    def now(self) -> datetime:
        given, self.next = self.next, self.next + timedelta(seconds=1)
        return given


def written(*events: tuple[str, Mapping[str, object]]) -> Lines:
    store = Lines()
    ledger = Ledger(store, Ticks())
    for type, fields in events:
        ledger.record(type, fields)
    return store


def parsed(store: Lines) -> list[dict[str, object]]:
    return [json.loads(line) for line in store.kept]


THREE: tuple[tuple[str, Mapping[str, object]], ...] = (
    ("run.started", {"inputs": {"contract": "sha256:" + "a" * 64}}),
    ("gate.finished", {"gate": "baseline", "verdict": "PASS"}),
    ("run.finished", {"state": "done"}),
)


def found(lines: list[str]) -> list[tuple[str, tuple[int, ...]]]:
    return [(finding.code, finding.lines) for finding in verify(lines)]


def rehashed(event: dict[str, object]) -> str:
    """The line of an event with its hash computed again, so that only the field edited differs."""
    event = {name: value for name, value in event.items() if name != "hash"}
    return canonical({**event, "hash": digest(event)})
