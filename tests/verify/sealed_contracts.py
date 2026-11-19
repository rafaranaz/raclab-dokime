"""A split contract, its sealed batch and a run of the gate `sealed-examples`, for its tests.

Each held-out example has a visible partner in a case of its own, kept visible as published, so
that the split drawn again holds out that example whatever the seed. The contract has besides a
case of a single example, `c-single`, and a case of two examples both published, `c-pub`, which
hold out nothing for each of the two reasons.
"""

import json

from dokime.contract.check import check
from dokime.contract.held_out import held_out_digest
from dokime.contract.model import Contract
from dokime.core.observation import ObservationLimits
from dokime.core.repository import RefusalError
from dokime.verify.result import GateResult
from dokime.verify.sealed import Batch, SealedExample, Unheld, make_canary, sealed_examples
from tests.verify.doubles import AuditedDouble, ObserverDouble, patch
from tests.verify.gates import IMAGE, PACK

IMPOSSIBLE = "0123456789abcdef0123456789abcdef"
BASE = "b" * 40

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
EXTRAS = ("E-s1", "E-q1", "E-q2")
UNHELD = (Unheld("R-new", "c-single", "single-example"), Unheld("R-new", "c-pub", "all-published"))


def held(name: str, origin: str = "human", case: str = "c") -> str:
    return (
        f"  - id: {name}\n    requirement: R-new\n    case: {case}\n    boundary: function\n"
        f"    target: p:f\n    origin: {origin}\n    steps:\n"
        f"      - input: {{args: [{_argument(name)}]}}\n        expect: {{returns: 2}}\n"
    )


def _argument(name: str) -> int:
    """A number of its own for each example, so that no two have the same steps."""
    return int.from_bytes(name.encode(), "big") % 1_000_000


def salt(number: int) -> bytes:
    return bytes([number]) * 16


def partner(number: int) -> str:
    return f"E-p{number}"


def split(*texts: tuple[str, str]) -> tuple[Contract, tuple[SealedExample, ...]]:
    """The contract after the split, with the held-out examples given as (id, text), each put in
    the case `c<n>` of its position."""
    sealed = tuple(
        SealedExample(
            id=name, salt=salt(n), text=text.replace("    case: c\n", f"    case: c{n}\n")
        )
        for n, (name, text) in enumerate(texts)
    )
    visible = "".join(held(partner(n), case=f"c{n}") for n in range(len(sealed)))
    visible += (
        held("E-s1", case="c-single") + held("E-q1", case="c-pub") + held("E-q2", case="c-pub")
    )
    entries = "".join(
        f"  - id: {s.id}\n    requirement: R-new\n    case: c{n}\n"
        f"    digest: {held_out_digest(s.salt, s.text)}\n"
        for n, s in enumerate(sealed)
    )
    checked = check(HEADER + "examples:\n" + visible + "held_out:\n" + entries)
    assert checked.contract is not None, checked.findings
    return checked.contract, sealed


def batch_of(contract: Contract, sealed: tuple[SealedExample, ...], seed: int = 7) -> Batch:
    """The batch that the seal of the contract gives."""
    order = [i for n, s in enumerate(sealed) for i in (partner(n), s.id)]
    return Batch(
        story=contract.story,
        base=BASE,
        seed=seed,
        order=(*order, *EXTRAS),
        kept_visible=(*(partner(n) for n in range(len(sealed))), "E-q1", "E-q2"),
        examples=sealed,
        unheld=UNHELD,
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
