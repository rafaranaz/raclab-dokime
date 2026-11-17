# SDD-EARS: EVIDENCE-046 EVIDENCE-087 EVIDENCE-088
import copy
from typing import Any

import pytest

from dokime.core.canonical import canonical
from dokime.evidence.schema import read_back
from dokime.evidence.statement import build
from tests.evidence.runs import STOPPED, changed, statement, stopped_at_contract


def stopped_gates() -> list[dict[str, Any]]:
    value: list[dict[str, Any]] = statement(stopped_at_contract())["predicate"]["gates"]
    return value


def test_a_gate_not_reached_is_written_with_its_reason() -> None:
    gates = stopped_gates()
    assert gates[1] == {"gate": "environment", "status": "not-reached", "reason": STOPPED}
    assert [gate["status"] for gate in gates] == (
        ["run"] + ["not-reached"] * 5 + ["not-applicable"] * 5
    )


def test_a_run_that_stopped_reads_back_without_a_finding() -> None:
    assert read_back(build(stopped_at_contract()).data) == ()


def whole_gates() -> list[dict[str, Any]]:
    value: list[dict[str, Any]] = statement()["predicate"]["gates"]
    return value


def swapped() -> list[dict[str, Any]]:
    gates = whole_gates()
    gates[0], gates[1] = gates[1], gates[0]
    return gates


@pytest.mark.parametrize(
    "listed",
    [
        swapped(),
        whole_gates()[:-1],
        [*whole_gates(), {"gate": "extra", "status": "not-applicable", "reason": "r"}],
    ],
)
def test_gates_that_are_not_those_of_the_audit_flow_in_order_are_refused(
    listed: list[dict[str, Any]],
) -> None:
    ((code, message),) = changed(("predicate/gates", listed))
    assert code == "evidence-schema"
    assert "predicate/gates" in message


def on_stopped(**fields: Any) -> list[tuple[str, str]]:
    """The findings of the statement of the stopped run with fields of its predicate changed."""
    value = copy.deepcopy(statement(stopped_at_contract()))
    value["predicate"].update(fields)
    return [(f.code, f.message) for f in read_back(canonical(value).encode())]


def test_a_gate_not_reached_after_gates_that_passed_is_refused() -> None:
    gates = stopped_gates()
    gates[0]["verdict"] = "PASS"
    found = on_stopped(gates=gates, verdict="PASS")
    assert {code for code, _ in found} == {"evidence-schema"}
    assert [message.split(" at ")[1].split(":")[0] for _, message in found] == [
        f"predicate/gates/{position}" for position in range(1, 6)
    ]


def test_a_gate_that_ran_after_one_not_reached_is_refused() -> None:
    gates = stopped_gates()
    gates[2] = {"gate": "baseline", "status": "run", "verdict": "PASS", "findings": []}
    ((code, message),) = on_stopped(gates=gates)
    assert code == "evidence-schema"
    assert "predicate/gates/2" in message


def test_a_gate_that_is_not_a_mapping_is_refused() -> None:
    gates: list[object] = list(stopped_gates())
    gates[0] = "contract"
    found = on_stopped(gates=gates)
    assert any("predicate/gates/0: is not a mapping" in message for _, message in found)
