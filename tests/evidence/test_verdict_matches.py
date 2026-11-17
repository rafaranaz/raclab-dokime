# SDD-EARS: EVIDENCE-086
from typing import Any

import pytest

from tests.evidence.runs import changed, statement


def gates_ran(**verdicts: str) -> list[dict[str, Any]]:
    """The gates of the whole run, each one that ran with PASS unless given another verdict."""
    gates: list[dict[str, Any]] = statement()["predicate"]["gates"]
    for gate in gates:
        if gate["status"] == "run":
            gate["verdict"] = verdicts.get(gate["gate"].replace("-", "_"), "PASS")
    return gates


@pytest.mark.parametrize("written", ["PASS", "ASK", "ERROR"])
def test_a_verdict_that_is_not_the_precedence_over_the_gates_is_refused(written: str) -> None:
    ((code, message),) = changed(("predicate/verdict", written))
    assert code == "evidence-schema"
    assert "predicate/verdict" in message


def test_a_predicate_where_no_gate_ran_is_refused() -> None:
    gates = [
        {"gate": gate["gate"], "status": "not-applicable", "reason": "not here"}
        for gate in statement()["predicate"]["gates"]
    ]
    ((code, message),) = changed(("predicate/gates", gates), ("predicate/verdict", "PASS"))
    assert code == "evidence-schema"
    assert "predicate/verdict" in message


@pytest.mark.parametrize(
    ("verdicts", "written"),
    [
        ({}, "PASS"),
        ({"baseline": "ASK"}, "ASK"),
        ({"baseline": "ASK", "visible_examples": "FAIL"}, "FAIL"),
        ({"contract": "FAIL", "environment": "ERROR", "baseline": "ASK"}, "ERROR"),
    ],
)
def test_the_precedence_over_the_gates_that_ran_is_accepted(
    verdicts: dict[str, str], written: str
) -> None:
    gates = gates_ran(**verdicts)
    assert changed(("predicate/gates", gates), ("predicate/verdict", written)) == []
