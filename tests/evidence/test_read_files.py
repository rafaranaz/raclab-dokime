# SDD-EARS: EVIDENCE-092 EVIDENCE-093
import copy
import json
from pathlib import Path
from typing import Any

import pytest

from dokime.core.canonical import canonical
from dokime.evidence.schema import read_back
from tests.evidence.runs import sealed, statement

FILES = Path(__file__).parent / "files"
CASE = {"code": "case-without-holdout", "what": "R-1", "case": "c-single", "reason": "one"}


def file(version: str) -> dict[str, Any]:
    value: dict[str, Any] = json.loads((FILES / f"{version}.statement.json").read_bytes())
    return value


def problems(value: dict[str, Any]) -> list[str]:
    return [f.message for f in read_back(canonical(value).encode()) if f.code == "evidence-schema"]


@pytest.mark.parametrize("version", ["v0.1", "v0.2", "v0.3"])
def test_a_file_of_an_earlier_version_reads_back_as_it_is(version: str) -> None:
    data = (FILES / f"{version}.statement.json").read_bytes()
    assert json.loads(data)["predicateType"].endswith(f"/conformance/{version}")
    assert read_back(data) == ()


def sealed_gate(value: dict[str, Any]) -> dict[str, Any]:
    (gate,) = [g for g in value["predicate"]["gates"] if g["gate"] == "sealed-examples"]
    found: dict[str, Any] = gate
    return found


@pytest.mark.parametrize("version", ["v0.1", "v0.2"])
def test_a_hold_out_in_a_file_of_an_earlier_version_is_refused(version: str) -> None:
    value = file(version)
    gate = sealed_gate(value)
    gate.clear()
    gate.update(sealed_gate(statement(sealed())))
    assert any("predicate/gates/10/holdout" in m for m in problems(value))


@pytest.mark.parametrize("version", ["v0.1", "v0.2"])
def test_a_case_without_holdout_in_a_file_of_an_earlier_version_is_refused(version: str) -> None:
    value = file(version)
    value["predicate"]["not_checked"].insert(0, dict(CASE))
    found = problems(value)
    assert any("not_checked/0/code" in m for m in found)
    assert any("not_checked/0/case" in m for m in found)


def test_a_hold_out_on_another_gate_of_v03_is_refused() -> None:
    value = statement(sealed())
    gates = value["predicate"]["gates"]
    gates[3]["holdout"] = copy.deepcopy(sealed_gate(value)["holdout"])
    assert any("gates/3/holdout" in m for m in problems(value))


def test_a_case_on_another_code_of_v03_is_refused() -> None:
    value = statement(sealed())
    entry = next(
        e for e in value["predicate"]["not_checked"] if e["code"] != "case-without-holdout"
    )
    entry["case"] = "c1"
    place = value["predicate"]["not_checked"].index(entry)
    assert any(f"not_checked/{place}/case" in m for m in problems(value))


def test_a_case_without_holdout_without_a_case_of_v03_is_refused() -> None:
    value = statement(sealed())
    entry = next(
        e for e in value["predicate"]["not_checked"] if e["code"] == "case-without-holdout"
    )
    del entry["case"]
    place = value["predicate"]["not_checked"].index(entry)
    assert any(f"not_checked/{place}/case" in m for m in problems(value))


def test_the_motive_of_v03_is_of_its_closed_list() -> None:
    value = statement(sealed())
    sealed_gate(value)["holdout"]["without_holdout"][0]["motive"] = "forgotten"
    assert any("holdout/without_holdout/0/motive" in m for m in problems(value))
