"""The aggregation of the gates of a state (ADR-0015, ADR-0034).

A work state of the flow lists its gates and closes with the aggregation of their verdicts: any
`ERROR` gives `ERROR`, else any `FAIL` gives `FAIL` and drops the `ASK` of the round, else any `ASK`
gives `ASK`, else `PASS`. Every gate of the state is listed in its order, so that the evidence can
show each one (INV-7): run, with its result, or not applicable, with the block or milestone that
builds it. A gate that this version builds and has no result is an error, never a pass, unless the
caller gives it as not applicable with a reason, as the gate of the sealed examples where the key is
not.
"""

from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum

from dokime.core.findings import Finding, summarise
from dokime.core.verdicts import Verdict
from dokime.verify.result import GateResult

BUILT = frozenset(
    {
        "contract",
        "environment",
        "baseline",
        "protected-paths",
        "existing-tests",
        "visible-examples",
        "repeatability",
    }
)
"""The gates of the table of the architecture that this version runs."""

NOT_BUILT: Mapping[str, str] = {
    "relations": "the gate is built in block B",
    "sealed-examples": "the gate is built in block B",
    "agent-run": "the gate is built in block C",
    "changed-line-coverage": "the gate is built in block D",
    "behaviour-differences": "the gate is built in block D",
    "delivery": "the gate is built in block E",
}
"""The other gates of the table of the architecture, with where each one is built."""


class Status(StrEnum):
    """How a gate of a state appears in the evidence."""

    RUN = "run"
    NOT_APPLICABLE = "not-applicable"


@dataclass(frozen=True)
class GateEntry:
    """A gate of a state: run with its result, or not applicable with its reason."""

    gate: str
    status: Status
    result: GateResult | None = None
    reason: str | None = None


@dataclass(frozen=True)
class StateOutcome:
    """Every gate of a state, the findings of the aggregation itself, and the verdict."""

    gates: tuple[GateEntry, ...]
    findings: tuple[Finding, ...]

    @property
    def verdict(self) -> Verdict:
        """The precedence of ADR-0015 over the gates that ran and the aggregation's findings."""
        run = [entry.result for entry in self.gates if entry.result is not None]
        found = [finding for result in run for finding in result.findings]
        return summarise((*found, *self.findings))


def aggregate_state(
    gates: tuple[str, ...],
    results: tuple[GateResult, ...],
    not_applicable: Mapping[str, str] | None = None,
) -> StateOutcome:
    """Aggregate the results of the gates of a state, listed in the order of the state."""
    absent = dict(not_applicable or {})
    findings: list[Finding] = []
    counted = Counter(result.gate for result in results)
    for gate in sorted(name for name, count in counted.items() if count > 1):
        findings.append(_error("gate-repeated", f"the gate {gate} has more than one result"))
    for gate in sorted(set(absent) & set(counted)):
        findings.append(
            _error("gate-repeated", f"the gate {gate} has a result and a reason not to apply")
        )
    for gate in sorted((set(counted) | set(absent)) - set(gates)):
        findings.append(
            _error("gate-not-of-the-state", f"the gate {gate} has a result but is not of the state")
        )
    by_gate = {result.gate: result for result in results}
    entries = []
    for gate in gates:
        if gate in NOT_BUILT:
            entries.append(
                GateEntry(gate=gate, status=Status.NOT_APPLICABLE, reason=NOT_BUILT[gate])
            )
        elif gate not in BUILT:
            findings.append(_error("gate-unknown", f"the gate {gate} is not in the table of gates"))
        elif gate in absent and gate not in by_gate:
            entries.append(GateEntry(gate=gate, status=Status.NOT_APPLICABLE, reason=absent[gate]))
        elif gate in by_gate:
            entries.append(GateEntry(gate=gate, status=Status.RUN, result=by_gate[gate]))
        else:
            findings.append(_error("gate-missing", f"the gate {gate} of the state has no result"))
    return StateOutcome(gates=tuple(entries), findings=tuple(findings))


def _error(code: str, message: str) -> Finding:
    return Finding(code=code, message=message, verdict=Verdict.ERROR)
