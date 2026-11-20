"""A base whose contract was sealed, a store double that opens its batch, and its history."""

from dataclasses import dataclass, field
from typing import Any

from dokime.contract.check import check
from dokime.contract.held_out import example_texts, held_out_digest
from dokime.core.repository import CommitName, FileVersion, RefusalError
from dokime.oracle.holdout import split
from dokime.verify.sealed import Batch, SealedExample, batch_bytes, make_canary, unheld_cases
from tests.interfaces.audit_runs import CONTRACT, CONTRACT_PATH, STORY, base_files
from tests.verify.doubles import HistoryDouble

SEALED_PATH = f".dokime/changes/{STORY}/sealed.age"
SEALED_BYTES = b"the sealed batch, as the store double reads it"
BATCH_BASE = CommitName("e" * 40)
SALT = bytes([7]) * 16
IMPOSSIBLE = "0123456789abcdef0123456789abcdef"
SECOND = """\
  - id: E-0003
    requirement: add-one
    case: normal
    boundary: function
    target: p:f
    origin: human
    steps:
      - input: {args: [5]}
        expect: {returns: 6}
"""
WHOLE = CONTRACT.decode() + SECOND
"""The contract before the seal: the case `normal` has two examples, `zero` one."""


def _seed() -> int:
    whole = check(WHOLE).contract
    assert whole is not None
    return next(s for s in range(100) if [e.id for e in split(whole, s).held_out] == ["E-0003"])


@dataclass(frozen=True)
class Seal:
    """The seal of `WHOLE`: the visible contract, the batch and its bytes."""

    visible: str
    batch: Batch
    content: bytes


def seal() -> Seal:
    whole = check(WHOLE).contract
    assert whole is not None
    seed = _seed()
    done = split(whole, seed)
    text = example_texts(WHOLE)["E-0003"]
    entry = (
        "held_out:\n  - id: E-0003\n    requirement: add-one\n    case: normal\n"
        f"    digest: {held_out_digest(SALT, text)}\n"
    )
    visible = WHOLE.replace(text, "") + entry
    written = check(visible).contract
    assert written is not None
    assert [h.id for h in written.held_out] == ["E-0003"]
    batch = Batch(
        story=STORY,
        base=BATCH_BASE.text,
        seed=seed,
        order=tuple(e.id for e in whole.examples),
        kept_visible=(),
        examples=(SealedExample("E-0003", SALT, text),),
        unheld=unheld_cases(whole, done),
        canary=make_canary(written, seed, "E-cana", IMPOSSIBLE),
    )
    return Seal(visible, batch, batch_bytes(batch))


SEAL = seal()


def sealed_files(**changes: bytes | None) -> dict[str, Any]:
    """The files of a base whose contract was sealed, with some changed or left out."""
    files = {CONTRACT_PATH: SEAL.visible.encode(), SEALED_PATH: SEALED_BYTES}
    return base_files(**{k.replace("/", "__"): v for k, v in files.items()} | changes)


def history(base: CommitName) -> HistoryDouble:
    """The history of the contract: nothing before the seal, the visible contract on the base."""
    return HistoryDouble({BATCH_BASE: (), base: (FileVersion(base, SEAL.visible.encode()),)})


@dataclass
class StoreDouble:
    """The sealed store with the key: it opens `SEALED_BYTES` into the content given, or refuses,
    and counts the times it was asked to open."""

    content: bytes = SEAL.content
    refusal: RefusalError | None = None
    opened: list[bytes] = field(default_factory=list)

    def seal(self, content: bytes, recipients: object) -> bytes:
        raise NotImplementedError

    def open(self, sealed: bytes) -> bytes:
        self.opened.append(sealed)
        if self.refusal is not None:
            raise self.refusal
        assert sealed == SEALED_BYTES
        return self.content
