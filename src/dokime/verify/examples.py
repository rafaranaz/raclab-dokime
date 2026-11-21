"""The gates `baseline` and `visible-examples`: the examples of the contract observed on a tree.

Both extract a tree into a directory of their own, ask the port that observes for every example of
the contract with the inputs of its steps, and compare each observation with its example through
the oracle. `baseline` observes the base as many times as `baseline.runs` says: an example that
holds in some runs and not in others asks, and is listed; otherwise an example of a `preserve`
requirement has to hold there, and one of a `new` or `change` requirement should not yet.
`visible-examples` observes the tree of the change of ADR-0058, the code of the patch with the tests
of the base: an example that does not hold fails the change, unless its origin is `model`, whose
expected result no person stands behind, so it asks (ADR-0013).
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
from dokime.core.policy import Policy
from dokime.core.repository import AuditedRepository, CommitName, RefusalError, TreeName
from dokime.core.runtime import Digest
from dokime.core.verdicts import Verdict
from dokime.oracle.compare import Comparison, compare
from dokime.packs.model import Pack
from dokime.verify.result import Checks, GateResult, checks_of
from dokime.verify.trees import base_tree, change_tree

BASELINE = "baseline"
VISIBLE = "visible-examples"
_SHOWN = 5
"""The differences of an example that a finding quotes; the rest are counted."""
_QUOTED = 200
"""The characters of a value that a finding quotes."""


def baseline(
    contract: Contract,
    policy: Policy,
    base: CommitName,
    image: Digest,
    repository: AuditedRepository,
    observer: ExampleObserver,
    limits: ObservationLimits,
) -> GateResult:
    """Check what the examples of the contract do on the base, as many times as the policy says."""
    kinds = {requirement.id: requirement.kind for requirement in contract.requirements}
    observed = _observe(
        BASELINE,
        contract,
        lambda: base_tree(repository, base),
        image,
        repository,
        observer,
        limits,
        policy.baseline_runs,
    )
    if isinstance(observed, GateResult):
        return observed
    findings, unstable = [], []
    for example, comparisons in zip(contract.examples, observed, strict=True):
        if len({comparison.holds for comparison in comparisons}) > 1:
            failing = next(comparison for comparison in comparisons if not comparison.holds)
            findings.append(_finding("example-varies-on-base", Verdict.ASK, example, failing))
            unstable.append(example.id)
            continue
        (comparison, *_) = comparisons
        preserved = kinds.get(example.requirement) == "preserve"
        if preserved and not comparison.holds:
            findings.append(
                _finding("preserved-example-fails-on-base", Verdict.FAIL, example, comparison)
            )
        elif not preserved and comparison.holds:
            findings.append(_finding("example-holds-on-base", Verdict.ASK, example, comparison))
    return GateResult(
        gate=BASELINE,
        findings=tuple(findings),
        unstable=tuple(unstable),
        checks=_checks(contract),
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
    """Check that the examples of the contract hold on the tree of the change."""
    observed = _observe(
        VISIBLE,
        contract,
        lambda: change_tree(pack, contract, base, patch, repository),
        image,
        repository,
        observer,
        limits,
        1,
    )
    if isinstance(observed, GateResult):
        return observed
    findings = []
    for example, (comparison,) in zip(contract.examples, observed, strict=True):
        if comparison.holds:
            continue
        if example.origin == "model":
            findings.append(_finding("model-example-fails", Verdict.ASK, example, comparison))
        else:
            findings.append(_finding("example-fails", Verdict.FAIL, example, comparison))
    return GateResult(gate=VISIBLE, findings=tuple(findings), checks=_checks(contract))


def _checks(contract: Contract) -> tuple[Checks, ...]:
    return checks_of(example.origin for example in contract.examples)


def _observe(
    gate: str,
    contract: Contract,
    tree: Callable[[], TreeName],
    image: Digest,
    repository: AuditedRepository,
    observer: ExampleObserver,
    limits: ObservationLimits,
    runs: int,
) -> list[list[Comparison]] | GateResult:
    """The comparisons of each example in each run, or the result of a gate that could not run."""
    if not contract.examples:
        return GateResult(gate=gate, findings=())
    requests = tuple(request_of(example) for example in contract.examples)
    try:
        composed = tree()
        with tempfile.TemporaryDirectory(prefix="dokime-examples-") as work:
            project = Path(work) / "project"
            project.mkdir()
            repository.extract(composed, project)
            observations = [observer.observe(image, project, requests, limits) for _ in range(runs)]
    except RefusalError as refusal:
        return GateResult(gate=gate, findings=(refusal.finding,))
    return [
        [compare(example, run[position]) for run in observations]
        for position, example in enumerate(contract.examples)
    ]


def request_of(example: Example) -> ExampleRequest:
    """The request that asks the observer for the steps of an example."""
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
