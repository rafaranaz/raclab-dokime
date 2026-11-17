"""What `evidence` is given of a run, in types of its own, since it imports nothing but `core`."""

from dataclasses import dataclass

from dokime.core.findings import Finding
from dokime.core.ledger import Head
from dokime.core.policy import Policy
from dokime.core.repository import CommitName, TreeName
from dokime.core.runtime import Digest
from dokime.core.verdicts import Verdict


@dataclass(frozen=True)
class Image:
    """The image built, and the digest of the manifest of the platform of its base image."""

    digest: Digest
    platform: Digest | None = None


@dataclass(frozen=True)
class Inputs:
    """What the run was given: the base, the effective policy and, when reached, the rest."""

    base: CommitName
    policy: Policy
    image: Image | None = None
    pack: bytes | None = None
    """The bytes of the file of the pack."""
    probe: Digest | None = None
    """The digest of the program that observes the examples."""


@dataclass(frozen=True)
class Requirement:
    """A requirement of the contract, with the origin of each of its examples."""

    id: str
    origins: tuple[str, ...]


@dataclass(frozen=True)
class Contract:
    """The contract read: the bytes of its file and its requirements."""

    text: bytes
    requirements: tuple[Requirement, ...]


@dataclass(frozen=True)
class Checks:
    """How many checks of one origin a gate ran."""

    origin: str
    total: int


@dataclass(frozen=True)
class GateRan:
    """A gate that ran, with the verdict it gave, its findings, its checks and what it left out."""

    gate: str
    verdict: Verdict
    findings: tuple[Finding, ...] = ()
    checks: tuple[Checks, ...] = ()
    unstable_tests: tuple[str, ...] = ()
    unstable_examples: tuple[str, ...] = ()


@dataclass(frozen=True)
class GateNotApplicable:
    """A gate that does not apply, with the reason."""

    gate: str
    reason: str


type Gate = GateRan | GateNotApplicable


@dataclass(frozen=True)
class Run:
    """A finished run: its subject, its verdict, what it was given, its gates and its ledger."""

    story: str
    tree: TreeName
    """The tree of the base with the whole patch, the result of the change."""
    patch: bytes
    verdict: Verdict
    harness: str
    """The version of the harness."""
    inputs: Inputs
    gates: tuple[Gate, ...]
    ledger: Head
    """The head of the ledger before the event `evidence.built`."""
    contract: Contract | None = None
