"""A split contract, its sealed batch and a run of the gate `sealed-examples`, for its tests."""

import json

from dokime.contract.check import check
from dokime.contract.held_out import held_out_digest
from dokime.contract.model import Contract
from dokime.core.observation import ObservationLimits
from dokime.core.repository import RefusalError
from dokime.verify.result import GateResult
from dokime.verify.sealed import Batch, SealedExample, make_canary, sealed_examples
from tests.verify.doubles import AuditedDouble, ObserverDouble, patch
from tests.verify.gates import IMAGE, PACK

IMPOSSIBLE = "0123456789abcdef0123456789abcdef"

HEADER = """\
format: 1
story: S-1
may_modify_tests: []
requirements:
  - id: R-new
    kind: new
    text: When the function is called with a number, the function shall return two.
    source: written
"""


def held(name: str, origin: str = "human", case: str = "c") -> str:
    return (
        f"  - id: {name}\n    requirement: R-new\n    case: {case}\n    boundary: function\n"
        f"    target: p:f\n    origin: {origin}\n    steps:\n"
        "      - input: {args: [1]}\n        expect: {returns: 2}\n"
    )


def salt(number: int) -> bytes:
    return bytes([number]) * 16


def split(*texts: tuple[str, str]) -> tuple[Contract, tuple[SealedExample, ...]]:
    """A contract with one visible example and the held-out ones given as (id, text)."""
    sealed = tuple(
        SealedExample(id=name, salt=salt(n), text=text) for n, (name, text) in enumerate(texts)
    )
    entries = "".join(
        f"  - id: {s.id}\n    requirement: R-new\n    case: c\n"
        f"    digest: {held_out_digest(s.salt, s.text)}\n"
        for s in sealed
    )
    text = HEADER + "examples:\n" + held("E-v1") + "held_out:\n" + entries
    checked = check(text)
    assert checked.contract is not None, checked.findings
    return checked.contract, sealed


def batch_of(contract: Contract, sealed: tuple[SealedExample, ...], seed: int = 7) -> Batch:
    return Batch(
        story=contract.story,
        seed=seed,
        examples=sealed,
        canary=make_canary(contract, seed, "E-cana", IMPOSSIBLE),
    )


def run(
    contract: Contract, batch: Batch, answers: dict[str, object]
) -> tuple[GateResult, ObserverDouble]:
    """Run the gate on a patch after which the observer returns `answers` by example."""
    repository, observer = AuditedDouble(), ObserverDouble()
    base = repository.add({"answers.json": b"{}", "src/p.py": b"code"})
    changed = patch({"answers.json": json.dumps(answers), "src/p.py": "new"})
    result = sealed_examples(
        PACK, contract, batch, base, changed, IMAGE, repository, observer, ObservationLimits()
    )
    return result, observer


def run_with(contract: Contract, batch: Batch, refusal: RefusalError) -> GateResult:
    """Run the gate with an observer that refuses."""
    repository = AuditedDouble()
    observer = ObserverDouble(refusal=refusal)
    base = repository.add({"answers.json": b"{}", "src/p.py": b"code"})
    changed = patch({"answers.json": "{}", "src/p.py": "new"})
    return sealed_examples(
        PACK, contract, batch, base, changed, IMAGE, repository, observer, ObservationLimits()
    )
