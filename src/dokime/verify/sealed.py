"""The sealed batch and the gate `sealed-examples` (ADR-0014, ADR-0072, ADR-0073).

The sealed batch is what the sealed store encrypts: the held-out examples of a contract, each with
its salt and its text as approved, the seed of the split and the canary, in canonical form
(ADR-0062). The canary is a copy of a held-out example, chosen by the seed, with only its first step
and, as its one expectation, a text of 32 hexadecimal digits that the caller draws at random: it
cannot hold. If it holds, the comparison accepts what it should not, the side of a false accept; an
observer that makes everything fail is not what it detects, since that gives rejections, the safe
side. The canary never counts as the failure of a requirement nor reaches the agent.

The gate checks first that the batch is the one the contract names, by the digest of the salt and
the text of each held-out example, and observes nothing otherwise. It reads each held-out example
from its text with the requirements of the contract, observes them and the canary on the tree of
the change, and words a held-out failure as the oracle does for the agent, with no value, input or
identifier.
"""

import json
import random
import re
from dataclasses import dataclass, replace

from dokime.contract.check import check
from dokime.contract.held_out import held_out_digest
from dokime.contract.model import Contract, Example, Step
from dokime.core.canonical import canonical
from dokime.core.findings import Finding
from dokime.core.observation import ExampleObserver, ObservationLimits
from dokime.core.repository import AuditedRepository, CommitName, RefusalError
from dokime.core.runtime import Digest
from dokime.core.verdicts import Verdict
from dokime.oracle.holdout import feedback
from dokime.packs.model import Pack
from dokime.verify.examples import _observe
from dokime.verify.result import GateResult, checks_of
from dokime.verify.trees import change_tree

SEALED = "sealed-examples"
NOT_HERE = "the key is not here"
_IMPOSSIBLE = re.compile(r"[0-9a-f]{32}")
_SALT = re.compile(r"[0-9a-f]{32}")


@dataclass(frozen=True)
class SealedExample:
    """A held-out example in the sealed batch: its id, its salt and its text as approved."""

    id: str
    salt: bytes
    text: str


@dataclass(frozen=True)
class Canary:
    """The canary of a batch: a copy of a held-out example whose expected value cannot hold."""

    id: str
    of: str
    expected: str


@dataclass(frozen=True)
class Batch:
    """What the sealed store encrypts for a contract."""

    story: str
    seed: int
    examples: tuple[SealedExample, ...]
    canary: Canary


def make_canary(contract: Contract, seed: int, canary_id: str, expected: str) -> Canary:
    """The canary of a contract: a held-out example chosen by the seed, with an impossible value."""
    chance = random.Random(seed)  # noqa: S311 - a draw anyone can repeat from the seed, not a secret
    return Canary(
        id=canary_id, of=chance.choice([h.id for h in contract.held_out]), expected=expected
    )


def batch_bytes(batch: Batch) -> bytes:
    """The content of a sealed batch, in canonical form."""
    return canonical(_mapping(batch)).encode()


def _mapping(batch: Batch) -> dict[str, object]:
    return {
        "format": 1,
        "story": batch.story,
        "seed": batch.seed,
        "examples": [{"id": e.id, "salt": e.salt.hex(), "text": e.text} for e in batch.examples],
        "canary": {"id": batch.canary.id, "of": batch.canary.of, "expected": batch.canary.expected},
    }


def read_batch(content: bytes) -> Batch:
    """The sealed batch of a content, or a refusal."""
    try:
        data = json.loads(content)
        batch = Batch(
            story=_text(data["story"]),
            seed=_natural(data["seed"]),
            examples=tuple(
                SealedExample(id=_text(e["id"]), salt=_salt(e["salt"]), text=_text(e["text"]))
                for e in data["examples"]
            ),
            canary=Canary(
                id=_text(data["canary"]["id"]),
                of=_text(data["canary"]["of"]),
                expected=_impossible(data["canary"]["expected"]),
            ),
        )
        if data["format"] != 1 or set(data) != {"format", "story", "seed", "examples", "canary"}:
            raise ValueError("not the fields of a batch")
        if batch_bytes(batch) != content:
            raise ValueError("not in canonical form")
    except (ValueError, KeyError, TypeError) as error:
        raise RefusalError("unreadable-batch", "the sealed batch cannot be read") from error
    return batch


def _text(value: object) -> str:
    if not isinstance(value, str):
        raise TypeError("not a text")
    return value


def _natural(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise TypeError("not a natural integer")
    return value


def _salt(value: object) -> bytes:
    if not isinstance(value, str) or _SALT.fullmatch(value) is None:
        raise ValueError("not a salt of 16 bytes in hexadecimal")
    return bytes.fromhex(value)


def _impossible(value: object) -> str:
    if not isinstance(value, str) or _IMPOSSIBLE.fullmatch(value) is None:
        raise ValueError("not 32 hexadecimal digits")
    return value


def sealed_examples(
    pack: Pack,
    contract: Contract,
    batch: Batch,
    base: CommitName,
    patch: bytes,
    image: Digest,
    repository: AuditedRepository,
    observer: ExampleObserver,
    limits: ObservationLimits,
) -> GateResult:
    """Check that the held-out examples hold on the tree of the change, and that the canary does
    not."""
    held = _held_examples(contract, batch)
    if held is None:
        message = "the sealed batch does not hold the held-out examples that the contract names"
        return GateResult(
            gate=SEALED,
            findings=(
                Finding(code="sealed-batch-mismatch", message=message, verdict=Verdict.ERROR),
            ),
        )
    canary = _canary(held, batch.canary)
    observed = _observe(
        SEALED,
        replace(contract, examples=(*held, canary)),
        lambda: change_tree(pack, contract, base, patch, repository),
        image,
        repository,
        observer,
        limits,
        1,
    )
    if isinstance(observed, GateResult):
        return observed
    *comparisons, (canary_seen,) = observed
    lines = {h.id: h.line for h in contract.held_out}
    findings = []
    for example, (comparison,) in zip(held, comparisons, strict=True):
        if comparison.holds:
            continue
        model = example.origin == "model"
        findings.append(
            Finding(
                code="sealed-model-example-fails" if model else "sealed-example-fails",
                message=feedback(example, comparison),
                verdict=Verdict.ASK if model else Verdict.FAIL,
                lines=(lines[example.id],),
            )
        )
    if canary_seen.holds:
        message = "the canary held: the comparison accepts an expectation that cannot hold"
        findings.append(Finding(code="canary-passed", message=message, verdict=Verdict.ERROR))
    return GateResult(
        gate=SEALED,
        findings=tuple(findings),
        checks=checks_of(example.origin for example in held),
    )


def _held_examples(contract: Contract, batch: Batch) -> tuple[Example, ...] | None:
    """The held-out examples read from the batch, in the order of the contract, or nothing when
    the batch is not the one that the contract names."""
    sealed = {s.id: s for s in batch.examples}
    if len(sealed) != len(batch.examples) or set(sealed) != {h.id for h in contract.held_out}:
        return None
    examples = []
    for entry in contract.held_out:
        one = sealed[entry.id]
        if held_out_digest(one.salt, one.text) != entry.digest:
            return None
        read = _read(contract, one.text)
        if read is None or (read.id, read.requirement, read.case) != (
            entry.id,
            entry.requirement,
            entry.case,
        ):
            return None
        examples.append(read)
    return tuple(examples)


def _read(contract: Contract, text: str) -> Example | None:
    """An example read from its text with the requirements of the contract."""
    requirements = "".join(
        "  - " + json.dumps({"id": r.id, "kind": r.kind, "text": r.text, "source": r.source}) + "\n"
        for r in contract.requirements
    )
    whole = (
        f"format: 1\nstory: {json.dumps(contract.story)}\nrequirements:\n{requirements}"
        f"examples:\n{text}"
    )
    checked = check(whole)
    if checked.contract is None or len(checked.contract.examples) != 1:
        return None
    return checked.contract.examples[0]


def _canary(held: tuple[Example, ...], canary: Canary) -> Example:
    """The canary as an example: the copy of a held-out example with an impossible expectation."""
    (copied,) = [example for example in held if example.id == canary.of]
    first = copied.steps[0]
    field = "stdout" if copied.boundary == "cli" else "returns"
    return replace(
        copied,
        id=canary.id,
        origin="human",
        steps=(Step(input=first.input, expect={field: canary.expected}),),
    )
