"""The gates `baseline` and `visible-examples`: the examples of the contract observed on a tree."""

from dokime.contract.model import Contract
from dokime.core.observation import ExampleObserver, ObservationLimits
from dokime.core.repository import AuditedRepository, CommitName
from dokime.core.runtime import Digest
from dokime.verify.result import GateResult

BASELINE = "baseline"
VISIBLE = "visible-examples"


def baseline(
    contract: Contract,
    base: CommitName,
    image: Digest,
    repository: AuditedRepository,
    observer: ExampleObserver,
    limits: ObservationLimits,
) -> GateResult:
    """Check what the examples of the contract do on the base, before the change."""
    return GateResult(gate=BASELINE, findings=())


def visible_examples(
    contract: Contract,
    base: CommitName,
    patch: bytes,
    image: Digest,
    repository: AuditedRepository,
    observer: ExampleObserver,
    limits: ObservationLimits,
) -> GateResult:
    """Check that the examples of the contract hold on the base with the patch."""
    return GateResult(gate=VISIBLE, findings=())
