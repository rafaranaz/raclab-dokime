# SDD-EARS: INTERFACES-090 INTERFACES-091 INTERFACES-092
from dokime.core.verdicts import Verdict
from dokime.evidence.schema import AUDIT_GATES
from dokime.interfaces.audit import STATES
from tests.interfaces.audit_runs import CONTRACT_PATH, audit, base_files

BUILT = ["contract", "environment", "baseline", "protected-paths", "existing-tests"]


def test_the_states_are_those_of_the_audit_flow_in_their_order() -> None:
    assert [state for state, _ in STATES] == [
        "checking-contract",
        "preparing",
        "baselining",
        "verifying",
        "sealed",
    ]
    assert dict(STATES)["verifying"][:3] == (
        "protected-paths",
        "existing-tests",
        "visible-examples",
    )


def test_the_gates_of_the_states_are_those_that_evidence_requires() -> None:
    assert tuple(gate for _, gates in STATES for gate in gates) == AUDIT_GATES


def test_a_change_that_passes_goes_through_every_state() -> None:
    done = audit()
    assert done.audited.verdict is Verdict.PASS
    statuses = {gate["gate"]: gate["status"] for gate in done.gates()}
    assert [gate for gate, status in statuses.items() if status == "run"] == [
        *BUILT,
        "visible-examples",
    ]
    assert {status for gate, status in statuses.items() if gate not in BUILT} >= {"not-applicable"}
    assert [gate["gate"] for gate in done.gates()] == list(AUDIT_GATES)


def test_a_state_that_does_not_pass_stops_the_run() -> None:
    done = audit(base_files(**{CONTRACT_PATH.replace("/", "__"): None}))
    assert done.audited.verdict is Verdict.ERROR
    gates = {gate["gate"]: gate for gate in done.gates()}
    assert gates["contract"]["status"] == "run"
    for name in (
        "environment",
        "baseline",
        "protected-paths",
        "existing-tests",
        "visible-examples",
    ):
        assert gates[name]["status"] == "not-reached"
        assert "checking-contract" in gates[name]["reason"]
        assert "ERROR" in gates[name]["reason"]
    assert gates["relations"]["status"] == "not-applicable"
    assert done.runtime.builds == []


def test_a_baseline_that_fails_stops_before_the_verification() -> None:
    files = base_files(**{"answers.json": b'{"E-0001": 1, "E-0002": 7}'})
    done = audit(files)
    assert done.audited.verdict is Verdict.FAIL
    statuses = {gate["gate"]: gate["status"] for gate in done.gates()}
    assert statuses["baseline"] == "run"
    assert statuses["protected-paths"] == statuses["visible-examples"] == "not-reached"
