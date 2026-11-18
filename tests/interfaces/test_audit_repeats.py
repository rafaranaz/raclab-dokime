# SDD-EARS: INTERFACES-140 INTERFACES-141 INTERFACES-142 INTERFACES-143 INTERFACES-144
import json
from typing import Any

import pytest

from dokime.core.verdicts import Verdict
from dokime.interfaces import audit as audit_module
from dokime.verify import aggregate
from tests.interfaces.audit_runs import (
    CONTRACT_PATH,
    TEST,
    ObservesRecorded,
    audit,
    base_files,
    change,
)
from tests.interfaces.test_audit_images import RefusesTheBuildsOfTheChange


@pytest.fixture
def repeating(monkeypatch: pytest.MonkeyPatch) -> None:
    """The gate repeatability built, as the pull request after this one leaves it."""
    built = aggregate.BUILT | {"repeatability"}
    not_built = {k: v for k, v in aggregate.NOT_BUILT.items() if k != "repeatability"}
    for module in (audit_module, aggregate):
        monkeypatch.setattr(module, "BUILT", built)
        monkeypatch.setattr(module, "NOT_BUILT", not_built)


def with_outcomes(*runs: str) -> bytes:
    return change(**{"outcomes.json": json.dumps([{TEST: outcome} for outcome in runs])})


def gates(statement: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {gate["gate"]: gate for gate in statement["predicate"]["gates"]}


@pytest.mark.usefixtures("repeating")
def test_the_worst_verdict_of_each_gate_enters_whatever_the_order_of_the_runs() -> None:
    first_passes = audit(changed=with_outcomes("passed", "failed"))
    first_fails = audit(changed=with_outcomes("failed", "passed"))
    for done in (first_passes, first_fails):
        assert done.audited.verdict is Verdict.FAIL
        listed = gates(done.statement())
        assert listed["existing-tests"]["verdict"] == "FAIL"
        assert [f["code"] for f in listed["existing-tests"]["findings"]] == ["existing-test-fails"]
        assert listed["repeatability"]["verdict"] == "ASK"
        assert [f["code"] for f in listed["repeatability"]["findings"]] == ["verdict-varies"]
    one, other = gates(first_passes.statement()), gates(first_fails.statement())
    for listed in (one, other):
        for finding in listed["repeatability"]["findings"]:
            del finding["untrusted"]
    assert one == other


@pytest.mark.usefixtures("repeating")
def test_the_gates_of_verifying_run_as_many_times_as_the_policy_says() -> None:
    policy = b"format: 1\nbaseline:\n  runs: 2\nverification:\n  runs: 3\n"
    observer = ObservesRecorded()
    done = audit(base_files(**{".dokime__policy.yaml": policy}), observer=observer)
    assert len(observer.calls) == 2 + 3
    assert done.statement()["predicate"]["repeated"] == {"runs": 3, "consistent": True}


def test_without_repeatability_the_gates_of_verifying_run_once() -> None:
    observer = ObservesRecorded()
    done = audit(observer=observer)
    assert len(observer.calls) == 2 + 1
    assert "repeated" not in done.statement()["predicate"]


@pytest.mark.usefixtures("repeating")
def test_repeated_says_whether_the_runs_were_consistent() -> None:
    varies = audit(changed=with_outcomes("passed", "failed"))
    assert varies.statement()["predicate"]["repeated"] == {"runs": 2, "consistent": False}


@pytest.mark.usefixtures("repeating")
def test_an_audit_stopped_before_the_verification_has_no_repeated() -> None:
    done = audit(base_files(**{CONTRACT_PATH.replace("/", "__"): None}))
    assert done.audited.verdict is Verdict.ERROR
    assert "repeated" not in done.statement()["predicate"]


@pytest.mark.usefixtures("repeating")
def test_the_number_of_the_run_is_recorded_in_the_events_of_the_gates() -> None:
    events = audit().events()
    runs = [
        (e["type"], e["gate"], e.get("run"))
        for e in events
        if e["type"] in ("gate.started", "gate.finished") and e["gate"] == "existing-tests"
    ]
    assert runs == [
        ("gate.started", "existing-tests", 1),
        ("gate.finished", "existing-tests", 1),
        ("gate.started", "existing-tests", 2),
        ("gate.finished", "existing-tests", 2),
    ]


@pytest.mark.usefixtures("repeating")
def test_the_image_of_the_change_is_built_once_and_recorded() -> None:
    observer = ObservesRecorded()
    done = audit(observer=observer)
    *_, first, second = observer.images
    assert first == second
    inputs = done.statement()["predicate"]["inputs"]
    assert inputs["change_image"] == {"digest": first.text}
    assert inputs["image"]["digest"] != first.text


@pytest.mark.usefixtures("repeating")
def test_a_refused_image_of_the_change_is_refused_once_for_every_run() -> None:
    done = audit(runtime=RefusesTheBuildsOfTheChange())
    visible = gates(done.statement())["visible-examples"]
    assert [(f["code"], f["verdict"]) for f in visible["findings"]] == [("build-failed", "ERROR")]
    finished = [
        e for e in done.events() if e["type"] == "gate.finished" and e["gate"] == "visible-examples"
    ]
    assert [(e["run"], e["verdict"]) for e in finished] == [(1, "ERROR"), (2, "ERROR")]
    assert "change_image" not in done.statement()["predicate"]["inputs"]
