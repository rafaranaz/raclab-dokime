# SDD-EARS: CORPUS-089 CORPUS-090 CORPUS-091
import tomllib
from pathlib import Path

from tests.corpus.cases import ACTIVE, CASES, GATES, RUNNABLE

WITHDRAWN = tomllib.loads((Path(__file__).parent / "withdrawn.toml").read_text())["withdrawn"]
FIELDS = {"key", "reason", "first_run", "key_given", "verdict", "failing_gate"}


def test_each_withdrawn_case_keeps_its_reason_and_its_first_run() -> None:
    keys = {case.key for case in CASES}
    for entry in WITHDRAWN:
        assert set(entry) - {"replaced_by"} == FIELDS, entry["key"]
        assert entry["key"] in keys
        assert entry["reason"].strip()
        assert entry["first_run"].strip()
        assert isinstance(entry["key_given"], bool)
        assert entry["verdict"] in ("PASS", "FAIL", "ASK", "ERROR")
        assert entry["failing_gate"] in ("", *GATES)
        assert (entry["verdict"] == "FAIL") == bool(entry["failing_gate"])


def test_a_replacement_named_is_a_case_that_is_not_withdrawn() -> None:
    withdrawn = {entry["key"] for entry in WITHDRAWN}
    active = {case.key for case in CASES} - withdrawn
    for entry in WITHDRAWN:
        for key in entry.get("replaced_by", []):
            assert key in active, (entry["key"], key)


def test_a_withdrawn_case_is_left_out_of_the_audit_and_the_count() -> None:
    withdrawn = {entry["key"] for entry in WITHDRAWN}
    assert withdrawn
    assert not withdrawn & {case.key for case in RUNNABLE}
    assert not withdrawn & {case.key for case in ACTIVE}
