# SDD-EARS: EVIDENCE-086
import pytest

from dokime.core.verdicts import Verdict
from tests.evidence.runs import changed, statement


def ran(*verdicts: str) -> list[dict[str, object]]:
    return [
        {"gate": f"gate-{n}", "status": "run", "verdict": v, "findings": []}
        for n, v in enumerate(verdicts)
    ]


NOT_APPLICABLE = {"gate": "sealed-examples", "status": "not-applicable", "reason": "block B"}


@pytest.mark.parametrize("written", ["PASS", "ASK", "ERROR"])
def test_a_verdict_that_is_not_the_precedence_over_the_gates_is_refused(written: str) -> None:
    ((code, message),) = changed(("predicate/verdict", written))
    assert code == "evidence-schema"
    assert "predicate/verdict" in message


@pytest.mark.parametrize("gates", [[], [NOT_APPLICABLE]])
def test_a_predicate_where_no_gate_ran_is_refused(gates: list[object]) -> None:
    ((code, message),) = changed(("predicate/gates", gates), ("predicate/verdict", "PASS"))
    assert code == "evidence-schema"
    assert "predicate/verdict" in message


@pytest.mark.parametrize(
    ("verdicts", "written"),
    [
        (("PASS",), "PASS"),
        (("PASS", "ASK"), "ASK"),
        (("ASK", "FAIL", "PASS"), "FAIL"),
        (("FAIL", "ERROR", "ASK"), "ERROR"),
    ],
)
def test_the_precedence_over_the_gates_that_ran_is_accepted(
    verdicts: tuple[str, ...], written: str
) -> None:
    gates = [*ran(*verdicts), NOT_APPLICABLE]
    assert changed(("predicate/gates", gates), ("predicate/verdict", written)) == []
    assert statement()["predicate"]["verdict"] == Verdict.FAIL.value
