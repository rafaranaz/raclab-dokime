# SDD-EARS: EVIDENCE-097 EVIDENCE-098
import json
from pathlib import Path
from typing import Any

import pytest

from dokime.core.canonical import canonical
from dokime.evidence.schema import read_back
from tests.evidence.runs import relating, statement

FILES = Path(__file__).parent / "files"
RECORD = {"seed": 1, "failed": [{"relation": "L1", "example": "E-1", "order": [1, 0]}]}


def problems(value: dict[str, Any]) -> list[str]:
    return [f.message for f in read_back(canonical(value).encode()) if f.code == "evidence-schema"]


def gate(value: dict[str, Any], name: str) -> dict[str, Any]:
    (found,) = [g for g in value["predicate"]["gates"] if g["gate"] == name]
    entry: dict[str, Any] = found
    return entry


@pytest.mark.parametrize("version", ["v0.1", "v0.2", "v0.3"])
def test_a_record_of_relations_in_a_file_of_an_earlier_version_is_refused(version: str) -> None:
    value: dict[str, Any] = json.loads((FILES / f"{version}.statement.json").read_bytes())
    entry = gate(value, "relations")
    entry.clear()
    entry.update(gate(statement(relating()), "relations"))
    assert any("predicate/gates/6/relations" in m for m in problems(value))


def test_a_record_of_relations_on_another_gate_of_v04_is_refused() -> None:
    value = statement(relating())
    value["predicate"]["gates"][3]["relations"] = dict(RECORD)
    assert any("gates/3/relations" in m for m in problems(value))


@pytest.mark.parametrize("order", [[0, 0], [1, 2], [-1, 0], ["0", "1"]])
def test_an_order_that_is_not_the_indices_of_its_items_is_refused(order: list[object]) -> None:
    value = statement(relating())
    gate(value, "relations")["relations"]["failed"][0]["order"] = order
    assert any("relations/failed/0/order" in m for m in problems(value))
