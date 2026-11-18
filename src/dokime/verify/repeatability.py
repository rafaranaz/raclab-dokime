"""The gate `repeatability`: the verdicts of the gates in the runs of the verification.

The verification runs as many times as `verification.runs` of the policy says (ADR-0054), and
`interfaces` gives this gate the results of the gates of each run. A gate whose verdict differs
between two runs asks, since a verdict that changes between runs of the same change is never an
accept. Runs that do not hold the same gates, once each, are an error of the harness. The
findings follow the gates in the order the runs list them.
"""

from collections import Counter
from collections.abc import Sequence

from dokime.core.findings import Finding
from dokime.core.verdicts import Verdict
from dokime.verify.result import GateResult

GATE = "repeatability"
MINIMUM = 2
"""The fewest runs that can be compared."""


def repeatability(runs: Sequence[Sequence[GateResult]]) -> GateResult:
    """Compare, gate by gate, the verdicts of the runs of the verification."""
    if len(runs) < MINIMUM:
        noun = "run" if len(runs) == 1 else "runs"
        raise ValueError(
            f"the gate {GATE} compares at least {MINIMUM} runs, and {len(runs)} {noun} were given"
        )
    counted = [Counter(result.gate for result in run) for run in runs]
    gates = list(dict.fromkeys(result.gate for run in runs for result in run))
    findings = []
    for gate in gates:
        if any(count[gate] != 1 for count in counted):
            findings.append(
                Finding(
                    code="runs-differ",
                    message=f"the gate {gate} does not have one result in each run",
                    verdict=Verdict.ERROR,
                )
            )
            continue
        verdicts = [next(r.verdict for r in run if r.gate == gate) for run in runs]
        if len(set(verdicts)) > 1:
            listed = ", ".join(verdict.value for verdict in verdicts)
            findings.append(
                Finding(
                    code="verdict-varies",
                    message=f"the gate {gate} gave different verdicts in the runs: {listed}",
                    verdict=Verdict.ASK,
                )
            )
    return GateResult(gate=GATE, findings=tuple(findings))
