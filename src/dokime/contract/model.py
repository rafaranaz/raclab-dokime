"""The contract as the rest of the harness uses it, once its text has been checked."""

from collections.abc import Mapping
from dataclasses import dataclass

from dokime.contract.expectations import Expected
from dokime.core.findings import Finding, summarise
from dokime.core.verdicts import Verdict


@dataclass(frozen=True)
class Requirement:
    """What the change has to do, in EARS. Its kind fixes what its examples do before the change."""

    id: str
    kind: str
    text: str
    source: str
    replaces: str | None
    line: int


@dataclass(frozen=True)
class Step:
    """One input given at the boundary and what is expected to be observed."""

    input: Mapping[str, Expected]
    expect: Mapping[str, Expected]


@dataclass(frozen=True)
class Example:
    """A list of steps at a boundary, approved by a person or proposed by a model."""

    id: str
    requirement: str
    case: str
    boundary: str
    target: str
    description: str | None
    origin: str
    steps: tuple[Step, ...]
    line: int


@dataclass(frozen=True)
class Relation:
    """A relation of the closed catalogue that the target has to keep."""

    id: str
    requirement: str
    relation: str
    target: str
    over: str | None
    line: int


@dataclass(frozen=True)
class Contract:
    """The requirements, the examples and the relations of one change."""

    story: str
    may_modify_tests: tuple[str, ...]
    requirements: tuple[Requirement, ...]
    examples: tuple[Example, ...]
    relations: tuple[Relation, ...]


@dataclass(frozen=True)
class Checked:
    """The result of checking the text of a contract.

    The contract is missing when a finding has the verdict `FAIL` or `ERROR`.
    """

    contract: Contract | None
    findings: tuple[Finding, ...]

    @property
    def verdict(self) -> Verdict:
        """The verdict that the findings give: `PASS` when there are none."""
        return summarise(self.findings)
