"""The gates `baseline` and `visible-examples`: the examples of the contract observed on a tree.

Both extract a tree into a directory of their own, ask the port that observes for every example of
the contract with the inputs of its steps, and compare each observation with its example through
the oracle. `baseline` observes the base: an example of a `preserve` requirement has to hold there,
and one of a `new` or `change` requirement should not yet. `visible-examples` observes the tree of
the change of ADR-0058, the code of the patch with the tests of the base: an example that does not
hold fails the change, unless its origin is `model`, whose expected result no person stands behind,
so it asks (ADR-0013).
"""

import tempfile
from collections.abc import Callable
from pathlib import Path

from dokime.contract.model import Contract, Example
from dokime.core.findings import Finding
from dokime.core.observation import (
    Boundary,
    ExampleObserver,
    ExampleRequest,
    ObservationLimits,
)
from dokime.core.repository import AuditedRepository, CommitName, RefusalError, TreeName
from dokime.core.runtime import Digest
from dokime.core.verdicts import Verdict
from dokime.oracle.compare import Comparison, compare
from dokime.packs.model import Pack
from dokime.verify.result import GateResult
from dokime.verify.trees import base_tree, change_tree

BASELINE = "baseline"
VISIBLE = "visible-examples"
_SHOWN = 5
"""The differences of an example that a finding quotes; the rest are counted."""
_QUOTED = 200
"""The characters of a value that a finding quotes."""


def baseline(
    contract: Contract,
    base: CommitName,
    image: Digest,
    repository: AuditedRepository,
    observer: ExampleObserver,
    limits: ObservationLimits,
) -> GateResult:
    """Check what the examples of the contract do on the base, before the change."""
    kinds = {requirement.id: requirement.kind for requirement in contract.requirements}

    def judge(example: Example, comparison: Comparison) -> Finding | None:
        preserved = kinds.get(example.requirement) == "preserve"
        if preserved and not comparison.holds:
            return _finding("preserved-example-fails-on-base", Verdict.FAIL, example, comparison)
        if not preserved and comparison.holds:
            return _finding("example-holds-on-base", Verdict.ASK, example, comparison)
        return None

    return _gate(
        BASELINE,
        contract,
        lambda: base_tree(repository, base),
        image,
        repository,
        observer,
        limits,
        judge,
    )


def visible_examples(
    pack: Pack,
    contract: Contract,
    base: CommitName,
    patch: bytes,
    image: Digest,
    repository: AuditedRepository,
    observer: ExampleObserver,
    limits: ObservationLimits,
) -> GateResult:
    """Check that the examples of the contract hold on the base with the patch."""

    def judge(example: Example, comparison: Comparison) -> Finding | None:
        if comparison.holds:
            return None
        if example.origin == "model":
            return _finding("model-example-fails", Verdict.ASK, example, comparison)
        return _finding("example-fails", Verdict.FAIL, example, comparison)

    return _gate(
        VISIBLE,
        contract,
        lambda: change_tree(pack, contract, base, patch, repository),
        image,
        repository,
        observer,
        limits,
        judge,
    )


def _gate(
    gate: str,
    contract: Contract,
    tree: Callable[[], TreeName],
    image: Digest,
    repository: AuditedRepository,
    observer: ExampleObserver,
    limits: ObservationLimits,
    judge: Callable[[Example, Comparison], Finding | None],
) -> GateResult:
    if not contract.examples:
        return GateResult(gate=gate, findings=())
    requests = tuple(_request(example) for example in contract.examples)
    try:
        composed = tree()
        with tempfile.TemporaryDirectory(prefix="dokime-examples-") as work:
            project = Path(work) / "project"
            project.mkdir()
            repository.extract(composed, project)
            observations = observer.observe(image, project, requests, limits)
    except RefusalError as refusal:
        return GateResult(gate=gate, findings=(refusal.finding,))
    findings = []
    for example, observation in zip(contract.examples, observations, strict=True):
        found = judge(example, compare(example, observation))
        if found is not None:
            findings.append(found)
    return GateResult(gate=gate, findings=tuple(findings))


def _request(example: Example) -> ExampleRequest:
    return ExampleRequest(
        example=example.id,
        boundary=Boundary(example.boundary),
        target=example.target,
        inputs=tuple(dict(step.input) for step in example.steps),
    )


def _finding(code: str, verdict: Verdict, example: Example, comparison: Comparison) -> Finding:
    if comparison.holds:
        said = "every expectation of its steps held"
    else:
        shown = [
            f"step {d.step} {d.part}: expected {_quote(d.expected)}, observed {_quote(d.observed)}"
            for d in comparison.differences[:_SHOWN]
        ]
        hidden = len(comparison.differences) - _SHOWN
        said = "; ".join(shown) + (f"; and {hidden} more" if hidden > 0 else "")
    return Finding(
        code=code,
        message=f"the example {example.id} of {example.requirement}: {said}",
        verdict=verdict,
        lines=(example.line,),
    )


def _quote(value: object) -> str:
    text = repr(value)
    return text if len(text) <= _QUOTED else text[:_QUOTED] + "…"
