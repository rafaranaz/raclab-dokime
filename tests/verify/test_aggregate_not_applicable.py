# SDD-EARS: VERIFY-127 VERIFY-128
from dokime.core.verdicts import Verdict
from dokime.verify.aggregate import GateEntry, Status, aggregate_state
from tests.verify.test_aggregate import result


def test_a_built_gate_given_as_not_applicable_is_listed_with_its_reason() -> None:
    outcome = aggregate_state(
        ("baseline", "visible-examples"),
        (result("baseline"),),
        {"visible-examples": "the key is not here"},
    )
    assert outcome.verdict is Verdict.PASS
    assert outcome.findings == ()
    assert outcome.gates[1] == GateEntry(
        gate="visible-examples", status=Status.NOT_APPLICABLE, reason="the key is not here"
    )


def test_a_gate_given_as_not_applicable_with_a_result_is_an_error() -> None:
    outcome = aggregate_state(
        ("baseline",), (result("baseline"),), {"baseline": "the key is not here"}
    )
    assert outcome.verdict is Verdict.ERROR
    assert [(f.code, "baseline" in f.message) for f in outcome.findings] == [
        ("gate-repeated", True)
    ]


def test_a_gate_not_of_the_state_given_as_not_applicable_is_an_error() -> None:
    outcome = aggregate_state(("baseline",), (result("baseline"),), {"existing-tests": "why"})
    assert outcome.verdict is Verdict.ERROR
    assert [(f.code, "existing-tests" in f.message) for f in outcome.findings] == [
        ("gate-not-of-the-state", True)
    ]
