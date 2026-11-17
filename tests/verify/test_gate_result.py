# SDD-EARS: VERIFY-001 VERIFY-002
import pytest

from dokime.core.findings import Finding
from dokime.core.verdicts import Verdict
from dokime.verify.result import GateResult


def finding(verdict: Verdict) -> Finding:
    return Finding(code="some-code", message="why", verdict=verdict)


def test_a_result_carries_its_gate_and_its_findings() -> None:
    found = (finding(Verdict.ASK),)
    result = GateResult(gate="protected-paths", findings=found)
    assert (result.gate, result.findings) == ("protected-paths", found)


def test_a_result_without_findings_passes() -> None:
    assert GateResult(gate="g", findings=()).verdict is Verdict.PASS


@pytest.mark.parametrize(
    ("verdicts", "expected"),
    [
        ((Verdict.ASK,), Verdict.ASK),
        ((Verdict.ASK, Verdict.FAIL), Verdict.FAIL),
        ((Verdict.FAIL, Verdict.ERROR, Verdict.ASK), Verdict.ERROR),
    ],
)
def test_the_verdict_of_a_result_summarises_its_findings(
    verdicts: tuple[Verdict, ...], expected: Verdict
) -> None:
    result = GateResult(gate="g", findings=tuple(finding(v) for v in verdicts))
    assert result.verdict is expected
