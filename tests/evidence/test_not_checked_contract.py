# SDD-EARS: EVIDENCE-060 EVIDENCE-061 EVIDENCE-062 EVIDENCE-066 EVIDENCE-067
from typing import Any

from tests.evidence.runs import predicate, run


def entries(given: list[dict[str, Any]]) -> list[tuple[str, str]]:
    return [(entry["code"], entry["what"]) for entry in given]


def test_what_was_not_checked_is_listed_by_code_in_its_order() -> None:
    assert entries(predicate()["not_checked"]) == [
        ("requirement-without-example", "R-2"),
        ("only-model-checks", "R-3"),
        ("test-excluded-unstable", "existing-tests"),
        ("example-unstable", "E-2"),
        ("outside-threat-model", "baseline"),
        ("outside-threat-model", "existing-tests"),
        ("outside-threat-model", "visible-examples"),
    ]


def test_without_a_contract_nothing_of_the_requirements_is_listed() -> None:
    codes = {entry["code"] for entry in predicate(run(contract=None))["not_checked"]}
    assert codes.isdisjoint({"no-holdout", "requirement-without-example", "only-model-checks"})


def test_each_entry_has_a_reason_of_its_own_for_its_code() -> None:
    given = predicate()["not_checked"]
    reasons: dict[str, set[str]] = {}
    for entry in given:
        assert entry["reason"]
        reasons.setdefault(entry["code"], set()).add(entry["reason"])
    assert all(len(found) == 1 for code, found in reasons.items() if code != "outside-threat-model")
    assert len({reason for found in reasons.values() for reason in found}) >= len(reasons)
