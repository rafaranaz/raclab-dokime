# SDD-EARS: EVIDENCE-094 EVIDENCE-095
from typing import Any

from dokime.evidence.run import RelationsRecord
from dokime.evidence.schema import read_back
from dokime.evidence.statement import build
from tests.evidence.runs import predicate, relating, run


def relations_entry(given: dict[str, Any]) -> dict[str, Any]:
    (entry,) = [g for g in given["gates"] if g["gate"] == "relations"]
    found: dict[str, Any] = entry
    return found


def test_the_gate_of_the_relations_records_the_seed_of_the_audit_and_what_failed() -> None:
    assert relations_entry(predicate(relating()))["relations"] == {
        "seed": 20261121,
        "failed": [
            {"relation": "L1", "example": "E-1", "order": [2, 0, 1]},
            {"relation": "L2", "example": "E-2"},
        ],
    }


def test_a_record_with_nothing_failed_has_an_empty_list() -> None:
    entry = relations_entry(predicate(relating(RelationsRecord(seed=5))))
    assert entry["relations"] == {"seed": 5, "failed": []}


def test_a_gate_of_the_relations_without_a_record_writes_none_and_reads_back() -> None:
    for given in (run(), relating(None)):
        assert "relations" not in relations_entry(predicate(given))
        assert read_back(build(given).data) == ()
