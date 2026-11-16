"""The ledger of a run: events chained by their hashes (ADR-0023), kept in canonical form."""

import json
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import UTC
from typing import Protocol

from dokime.core.canonical import NotCanonicalError, canonical, digest
from dokime.core.clock import Clock
from dokime.core.findings import Finding
from dokime.core.verdicts import Verdict


class LedgerStore(Protocol):
    """Keeps the lines of a ledger."""

    def append(self, line: str) -> None:
        """Append one line."""
        ...

    def lines(self) -> tuple[str, ...]:
        """The lines, in the order they were appended."""
        ...


TYPES = frozenset(
    {
        "run.started",
        "run.finished",
        "state.entered",
        "gate.started",
        "gate.finished",
        "human.asked",
        "human.answered",
        "model.called",
        "agent.started",
        "agent.finished",
        "baseline.unstable",
        "budget.exhausted",
        "evidence.built",
    }
)
FIELDS = ("seq", "at", "type", "prev", "hash")


class LedgerError(ValueError):
    """An event the ledger refuses, or a store it cannot continue."""


@dataclass(frozen=True)
class Event:
    """One event as it was written."""

    seq: int
    at: str
    type: str
    prev: str | None
    hash: str
    fields: Mapping[str, object]


class Ledger:
    """Records events through a store, stamped by a clock.

    Opened on a store that already holds events, it verifies them and continues their sequence
    and their chain; it refuses a store that does not verify.
    """

    def __init__(self, store: LedgerStore, clock: Clock) -> None:
        self._store = store
        self._clock = clock
        lines = store.lines()
        findings = verify(lines)
        if findings:
            raise LedgerError(f"the ledger in the store does not verify: {_listed(findings)}")
        last = json.loads(lines[-1]) if lines else None
        self._seq: int = last["seq"] if last else 0
        self._prev: str | None = last["hash"] if last else None

    def record(self, type: str, fields: Mapping[str, object]) -> Event:
        """Record an event of a type with its fields, and give it as it was written."""
        if type not in TYPES:
            raise LedgerError(f"{type!r} is not a type of event of the ledger")
        for name in FIELDS:
            if name in fields:
                raise LedgerError(f"the field {name!r} is a field of the ledger, not of an event")
        now = self._clock.now()
        if now.tzinfo is None or now.utcoffset() is None:
            raise LedgerError(f"the clock gave {now.isoformat()}, a time without a time zone")
        at = now.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        seq, prev = self._seq + 1, self._prev
        event = {**fields, "seq": seq, "at": at, "type": type, "prev": prev}
        hashed = digest(event)
        self._store.append(canonical({**event, "hash": hashed}))
        self._seq, self._prev = seq, hashed
        return Event(seq=seq, at=at, type=type, prev=prev, hash=hashed, fields=dict(fields))


@dataclass(frozen=True)
class Head:
    """What the evidence keeps of a ledger: the hash of its last event and how many there are."""

    hash: str | None
    events: int


def head(lines: Iterable[str]) -> Head:
    """Give the head of the lines of a ledger, which have to verify."""
    kept = tuple(lines)
    findings = verify(kept)
    if findings:
        raise LedgerError(f"the ledger does not verify, so it has no head: {_listed(findings)}")
    return Head(hash=json.loads(kept[-1])["hash"] if kept else None, events=len(kept))


def _listed(findings: Iterable[Finding]) -> str:
    return "; ".join(f"line {finding.lines[0]}: {finding.code}" for finding in findings)


def _fail(code: str, message: str, line: int) -> Finding:
    return Finding(code=code, message=message, verdict=Verdict.FAIL, lines=(line,))


def _is_event(value: object) -> bool:
    if not isinstance(value, dict) or not all(name in value for name in FIELDS):
        return False
    seq, prev = value["seq"], value["prev"]
    return (
        type(seq) is int
        and isinstance(value["at"], str)
        and value["type"] in TYPES
        and (prev is None or isinstance(prev, str))
        and isinstance(value["hash"], str)
    )


def verify(lines: Iterable[str], expected: Head | None = None) -> tuple[Finding, ...]:
    """Verify the lines of a ledger: each an event in canonical form, chained to the one before.

    A line that is not an event is reported and skipped, so the line after it is checked against
    the last event before it. The chain cannot show that its last events were removed or that it
    was written again from the start; with the head that the evidence keeps, it can.
    """
    findings: list[Finding] = []
    seq, prev, events = 0, None, 0
    for number, line in enumerate(lines, start=1):
        try:
            event = json.loads(line)
        except ValueError:
            event = None
        if not _is_event(event):
            findings.append(_fail("not-an-event", "the line is not an event of the ledger", number))
            continue
        findings.extend(_event(number, line, event, seq, prev))
        seq, prev, events = event["seq"], event["hash"], events + 1
    if expected is not None and (prev, events) != (expected.hash, expected.events):
        message = (
            f"the ledger ends at {prev} after {events} events, and the head expected is"
            f" {expected.hash} after {expected.events} events"
        )
        findings.append(_fail("wrong-head", message, max(events, 1)))
    return tuple(findings)


def _canonical_or_none(value: object) -> str | None:
    try:
        return canonical(value)
    except NotCanonicalError:
        return None


def _event(
    number: int, line: str, event: dict[str, object], seq: int, prev: str | None
) -> list[Finding]:
    """The findings of one event: its encoding, its hash and its place in the chain."""
    findings = []
    if _canonical_or_none(event) != line:
        message = "the line is not the canonical form of its event"
        findings.append(_fail("not-canonical", message, number))
    unhashed = {name: value for name, value in event.items() if name != "hash"}
    written = _canonical_or_none(unhashed)
    if written is None or digest(unhashed) != event["hash"]:
        findings.append(_fail("wrong-hash", "the hash is not the digest of the event", number))
    if event["prev"] != prev:
        should = "null" if prev is None else prev
        findings.append(_fail("broken-chain", f"prev should be {should}", number))
    if event["seq"] != seq + 1:
        findings.append(_fail("wrong-sequence", f"seq should be {seq + 1}", number))
    return findings
