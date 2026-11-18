# SDD-EARS: VERIFY-120 VERIFY-121 VERIFY-122 VERIFY-123 VERIFY-124 VERIFY-125 VERIFY-126
import pytest

from dokime.core.findings import Finding
from dokime.core.verdicts import Verdict
from dokime.verify.aggregate import GateEntry, Status, aggregate_state
from dokime.verify.result import GateResult

VERIFYING = (
    "protected-paths",
    "existing-tests",
    "visible-examples",
    "relations",
    "changed-line-coverage",
    "behaviour-differences",
    "repeatability",
)


def result(gate: str, *verdicts: Verdict) -> GateResult:
    findings = tuple(Finding(code="some-code", message="why", verdict=v) for v in verdicts)
    return GateResult(gate=gate, findings=findings)


def ran(*verdicts: tuple[Verdict, ...]) -> tuple[GateResult, ...]:
    built = ("protected-paths", "existing-tests", "visible-examples")
    gates = tuple(result(gate, *found) for gate, found in zip(built, verdicts, strict=True))
    return (*gates, result("repeatability"))


@pytest.mark.parametrize(
    ("verdicts", "expected"),
    [
        (((), (), ()), Verdict.PASS),
        (((), (Verdict.ASK,), ()), Verdict.ASK),
        (((Verdict.ASK,), (Verdict.FAIL,), ()), Verdict.FAIL),
        (((Verdict.FAIL,), (), (Verdict.ERROR,)), Verdict.ERROR),
    ],
)
def test_the_verdict_of_a_state_is_the_precedence_of_its_gates(
    verdicts: tuple[tuple[Verdict, ...], ...], expected: Verdict
) -> None:
    assert aggregate_state(VERIFYING, ran(*verdicts)).verdict is expected


def test_every_gate_of_the_state_is_listed_in_its_order() -> None:
    results = ran((), (Verdict.ASK,), ())
    outcome = aggregate_state(VERIFYING, tuple(reversed(results)))
    assert [entry.gate for entry in outcome.gates] == list(VERIFYING)
    assert outcome.gates[:3] == tuple(
        GateEntry(gate=r.gate, status=Status.RUN, result=r) for r in results[:3]
    )
    assert outcome.gates[6] == GateEntry(gate="repeatability", status=Status.RUN, result=results[3])
    assert outcome.findings == ()


@pytest.mark.parametrize(
    ("gate", "where"),
    [
        ("relations", "block B"),
        ("sealed-examples", "block B"),
        ("agent-run", "block C"),
        ("changed-line-coverage", "block D"),
        ("behaviour-differences", "block D"),
        ("delivery", "block E"),
    ],
)
def test_a_gate_not_built_is_not_applicable_with_where_it_is_built(gate: str, where: str) -> None:
    (entry,) = aggregate_state((gate,), ()).gates
    assert (entry.status, entry.result) == (Status.NOT_APPLICABLE, None)
    assert entry.reason is not None
    assert where in entry.reason


def test_a_state_whose_gates_are_all_not_applicable_passes() -> None:
    assert aggregate_state(("sealed-examples",), ()).verdict is Verdict.PASS


@pytest.mark.parametrize(
    "gate",
    [
        "contract",
        "environment",
        "baseline",
        "protected-paths",
        "existing-tests",
        "visible-examples",
        "repeatability",
    ],
)
def test_a_built_gate_without_a_result_is_an_error(gate: str) -> None:
    outcome = aggregate_state((gate,), ())
    assert outcome.verdict is Verdict.ERROR
    ((code, verdict, named),) = [(f.code, f.verdict, gate in f.message) for f in outcome.findings]
    assert (code, verdict, named) == ("gate-missing", Verdict.ERROR, True)


def test_a_result_of_a_gate_that_is_not_of_the_state_is_an_error() -> None:
    outcome = aggregate_state(("baseline",), (result("baseline"), result("existing-tests")))
    assert outcome.verdict is Verdict.ERROR
    assert [(f.code, "existing-tests" in f.message) for f in outcome.findings] == [
        ("gate-not-of-the-state", True)
    ]


def test_a_gate_not_in_the_table_is_an_error() -> None:
    outcome = aggregate_state(("baseline", "made-up"), (result("baseline"),))
    assert outcome.verdict is Verdict.ERROR
    assert [(f.code, "made-up" in f.message) for f in outcome.findings] == [("gate-unknown", True)]


def test_two_results_of_one_gate_are_an_error() -> None:
    outcome = aggregate_state(("baseline",), (result("baseline"), result("baseline")))
    assert outcome.verdict is Verdict.ERROR
    assert [(f.code, "baseline" in f.message) for f in outcome.findings] == [
        ("gate-repeated", True)
    ]
