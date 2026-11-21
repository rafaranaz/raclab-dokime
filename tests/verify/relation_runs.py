"""A contract with relations, an observer that answers from the input it is given, and a run of
the gate `relations`, for its tests."""

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from pathlib import Path

from dokime.contract.check import check
from dokime.contract.model import Contract
from dokime.core.observation import (
    Ending,
    ExampleObservation,
    ExampleRequest,
    Exited,
    ObservationLimits,
    Raised,
    Returned,
    StepObservation,
)
from dokime.core.repository import RefusalError
from dokime.core.runtime import Digest
from dokime.verify.relations import RelationsOutcome, relations
from tests.verify.doubles import AuditedDouble, patch
from tests.verify.gates import IMAGE, PACK

HEADER = """\
format: 1
story: S-1
may_modify_tests: []
requirements:
  - id: R-sort
    kind: new
    text: When the function is given a list, the function shall return it sorted.
    source: written
  - id: R-cli
    kind: new
    text: When the command is given a file of lines, the command shall print its lines sorted.
    source: written
"""


def example(name: str, requirement: str, target: str, given: str, steps: int = 1) -> str:
    boundary = "cli" if requirement == "R-cli" else "function"
    expect = "{exit: 0}" if boundary == "cli" else "{returns: []}"
    step = f"      - input: {given}\n        expect: {expect}\n"
    return (
        f"  - id: {name}\n    requirement: {requirement}\n    case: c-{name}\n"
        f"    boundary: {boundary}\n    target: {target}\n    origin: human\n    steps:\n"
        + step
        * steps
    )


EXAMPLES = (
    example("E-1", "R-sort", "p:sort", "{args: [[3, 1, 2]]}")
    + example("E-2", "R-sort", "p:sort", "{args: [[5, 4]]}")
    + example("E-3", "R-sort", "p:sort", "{args: [[9, 8]]}", steps=2)
    + example("E-4", "R-cli", "sortlines", '{args: [in.txt], files: {in.txt: "b\\na\\n"}}')
)


def contract(relations_text: str, examples: str = EXAMPLES) -> Contract:
    checked = check(HEADER + "examples:\n" + examples + "relations:\n" + relations_text)
    assert checked.contract is not None, checked.findings
    return checked.contract


ORDER = """\
  - id: L1
    requirement: R-sort
    relation: order-insensitive
    target: p:sort
    over: args[0]
"""
ONCE = """\
  - id: L2
    requirement: R-sort
    relation: idempotent
    target: p:sort
"""
LINES = """\
  - id: L3
    requirement: R-cli
    relation: order-insensitive
    target: sortlines
    over: in.txt
"""

type Behaviour = Callable[[str, Mapping[str, object]], StepObservation | None]


def sorting(target: str, given: Mapping[str, object]) -> StepObservation | None:
    """The program that sorts: a list returned sorted, the lines of a file printed sorted."""
    if target == "p:sort":
        args = given["args"]
        assert isinstance(args, list)
        return Returned(sorted(args[0]))
    files = given["files"]
    assert isinstance(files, dict)
    text = files["in.txt"]
    lines = sorted(text.splitlines())
    return Exited(exit=0, stdout="".join(f"{line}\n" for line in lines), stderr="", files=files)


@dataclass
class ComputingObserver:
    """The port that observes, answering each step from its input with a behaviour; `None` from
    the behaviour is a step that did not end, and a refusal is raised when given."""

    behaviour: Behaviour
    refusal: RefusalError | None = None
    calls: list[tuple[ExampleRequest, ...]] = field(default_factory=list)

    def observe(
        self,
        image: Digest,
        project: Path,
        requests: tuple[ExampleRequest, ...],
        limits: ObservationLimits,
    ) -> tuple[ExampleObservation, ...]:
        self.calls.append(requests)
        if self.refusal is not None:
            raise self.refusal
        observed = []
        for request in requests:
            steps = [self.behaviour(request.target, given) for given in request.inputs]
            if any(step is None for step in steps):
                observed.append(ExampleObservation(request.example, (), ending=Ending.TIME_LIMIT))
            else:
                observed.append(
                    ExampleObservation(request.example, tuple(s for s in steps if s is not None))
                )
        return tuple(observed)


def raising(target: str, given: Mapping[str, object]) -> StepObservation:
    return Raised(type="ValueError", qualified="builtins.ValueError", classes=(), message="no")


def run(
    of: Contract,
    observer: ComputingObserver,
    *,
    seed: int = 20261121,
    permutations: int = 2,
    repository: AuditedDouble | None = None,
) -> RelationsOutcome:
    repository = repository or AuditedDouble()
    base = repository.add({"src/p.py": b"code"})
    changed = patch({"src/p.py": "new"})
    return relations(
        PACK,
        of,
        base,
        changed,
        IMAGE,
        repository,
        observer,
        ObservationLimits(),
        seed,
        permutations,
    )
