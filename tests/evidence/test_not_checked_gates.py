# SDD-EARS: EVIDENCE-063 EVIDENCE-064 EVIDENCE-065
from dokime.core.verdicts import Verdict
from dokime.evidence.run import GateNotApplicable, GateRan
from tests.evidence.runs import TEST, gates_with, predicate, run


def test_an_unstable_test_is_listed_with_its_name_untrusted() -> None:
    (entry,) = [e for e in predicate()["not_checked"] if e["code"] == "test-excluded-unstable"]
    assert entry["what"] == "existing-tests"
    assert entry["untrusted"] == [{"label": "test", "text": TEST}]
    assert TEST not in entry["reason"]


def test_an_unstable_example_is_listed_by_its_id() -> None:
    (entry,) = [e for e in predicate()["not_checked"] if e["code"] == "example-unstable"]
    assert entry["what"] == "E-2"
    assert "untrusted" not in entry


def test_the_gates_that_run_the_code_under_test_in_process_are_outside_the_threat_model() -> None:
    gates = gates_with(
        GateRan("visible-examples", Verdict.PASS),
        GateNotApplicable("existing-tests", "not here"),
        GateRan("baseline", Verdict.PASS),
    )
    given = predicate(run(gates=gates, contract=None, verdict=Verdict.PASS))["not_checked"]
    assert [(e["code"], e["what"]) for e in given] == [
        ("outside-threat-model", "baseline"),
        ("outside-threat-model", "visible-examples"),
    ]
    assert all("process" in entry["reason"] for entry in given)


def test_the_reason_of_the_tests_differs_from_that_of_the_examples() -> None:
    given = predicate()["not_checked"]
    reason = {e["what"]: e["reason"] for e in given if e["code"] == "outside-threat-model"}
    assert reason["baseline"] == reason["visible-examples"] != reason["existing-tests"]
