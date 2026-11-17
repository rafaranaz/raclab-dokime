# SDD-EARS: EVIDENCE-040 EVIDENCE-041 EVIDENCE-042 EVIDENCE-043
from dokime.core.findings import Finding
from dokime.core.verdicts import Verdict
from dokime.evidence.run import GateRan
from tests.evidence.runs import FAILS, predicate, run


def test_every_gate_is_listed_in_the_order_given() -> None:
    names = [gate["gate"] for gate in predicate()["gates"]]
    assert names == [
        "contract",
        "baseline",
        "existing-tests",
        "visible-examples",
        "sealed-examples",
    ]


def test_a_gate_that_ran_has_its_verdict_findings_and_checks() -> None:
    visible = predicate()["gates"][3]
    assert visible == {
        "gate": "visible-examples",
        "status": "run",
        "verdict": "FAIL",
        "findings": [
            {
                "code": "example-fails",
                "verdict": "FAIL",
                "lines": [12],
                "untrusted": [{"label": "message", "text": FAILS.message}],
            }
        ],
        "checks": [{"origin": "human", "total": 1}, {"origin": "model", "total": 3}],
    }


def test_a_gate_without_checks_or_findings_has_neither_checks_nor_null() -> None:
    contract = predicate()["gates"][0]
    assert contract == {"gate": "contract", "status": "run", "verdict": "PASS", "findings": []}


def test_a_finding_without_lines_has_an_empty_list() -> None:
    bare = Finding(code="c", message="m", verdict=Verdict.FAIL)
    gate = GateRan("g", Verdict.FAIL, findings=(bare,))
    (written,) = predicate(run(gates=(gate,)))["gates"][0]["findings"]
    assert written["lines"] == []


def test_a_gate_that_does_not_apply_has_its_reason() -> None:
    sealed = predicate()["gates"][4]
    assert sealed == {
        "gate": "sealed-examples",
        "status": "not-applicable",
        "reason": "the gate is built in block B",
    }
