# SDD-EARS: VERIFY-140 VERIFY-141 VERIFY-142 VERIFY-143 VERIFY-144
import pytest

from dokime.core.findings import Finding
from dokime.core.verdicts import Verdict
from dokime.verify.repeatability import repeatability
from dokime.verify.result import GateResult


def result(gate: str, verdict: Verdict) -> GateResult:
    if verdict is Verdict.PASS:
        return GateResult(gate=gate, findings=())
    return GateResult(gate=gate, findings=(Finding(code="c", message="m", verdict=verdict),))


def run(**verdicts: Verdict) -> tuple[GateResult, ...]:
    return tuple(result(gate.replace("_", "-"), verdict) for gate, verdict in verdicts.items())


def codes(found: GateResult) -> list[tuple[str, Verdict]]:
    return [(f.code, f.verdict) for f in found.findings]


def test_runs_with_the_same_verdicts_pass() -> None:
    same = run(existing_tests=Verdict.FAIL, visible_examples=Verdict.PASS)
    found = repeatability([same, same, same])
    assert (found.gate, found.verdict, found.findings) == ("repeatability", Verdict.PASS, ())


def test_a_gate_whose_verdict_varies_asks_naming_its_verdicts() -> None:
    found = repeatability(
        [
            run(existing_tests=Verdict.PASS, visible_examples=Verdict.PASS),
            run(existing_tests=Verdict.FAIL, visible_examples=Verdict.PASS),
            run(existing_tests=Verdict.PASS, visible_examples=Verdict.PASS),
        ]
    )
    assert codes(found) == [("verdict-varies", Verdict.ASK)]
    message = found.findings[0].message
    assert "existing-tests" in message
    assert message.index("PASS") < message.index("FAIL") < message.rindex("PASS")
    assert found.verdict is Verdict.ASK


def test_each_gate_that_varies_has_its_finding() -> None:
    found = repeatability(
        [
            run(protected_paths=Verdict.PASS, existing_tests=Verdict.PASS),
            run(protected_paths=Verdict.ERROR, existing_tests=Verdict.ASK),
        ]
    )
    assert codes(found) == [("verdict-varies", Verdict.ASK)] * 2
    assert [
        "protected-paths" in found.findings[0].message,
        "existing-tests" in found.findings[1].message,
    ] == [True, True]


@pytest.mark.parametrize(
    "runs",
    [
        [run(existing_tests=Verdict.PASS), run(visible_examples=Verdict.PASS)],
        [run(existing_tests=Verdict.PASS), (*run(existing_tests=Verdict.PASS),) * 2],
    ],
)
def test_runs_that_do_not_have_the_same_gates_are_an_error(
    runs: list[tuple[GateResult, ...]],
) -> None:
    found = repeatability(runs)
    assert ("runs-differ", Verdict.ERROR) in codes(found)
    assert found.verdict is Verdict.ERROR


@pytest.mark.parametrize("count", [0, 1])
def test_fewer_than_two_runs_are_refused(count: int) -> None:
    with pytest.raises(ValueError, match=f"{count} run"):
        repeatability([run(existing_tests=Verdict.PASS)] * count)
