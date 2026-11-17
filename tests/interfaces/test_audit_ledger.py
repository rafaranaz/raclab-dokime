# SDD-EARS: INTERFACES-098 INTERFACES-099 INTERFACES-100
import json

import pytest

from dokime.core.verdicts import Verdict
from dokime.interfaces import audit as audit_module
from tests.interfaces.audit_runs import TEST, audit, base_files


def test_the_run_is_recorded_in_the_ledger() -> None:
    events = audit().events()
    kinds = [(e["type"], e.get("state") or e.get("gate")) for e in events]
    assert kinds[0] == ("run.started", None)
    assert ("state.entered", "checking-contract") in kinds
    assert kinds.index(("gate.started", "contract")) < kinds.index(("gate.finished", "contract"))
    assert ("gate.finished", "visible-examples") in kinds
    assert ("gate.started", "relations") not in kinds
    assert [k for k, _ in kinds[-2:]] == ["evidence.built", "run.finished"]
    assert events[-1]["verdict"] == "PASS"


def test_what_a_gate_left_out_as_unstable_is_recorded() -> None:
    varies = json.dumps([{TEST: "passed"}, {TEST: "failed"}]).encode()
    events = audit(base_files(**{"outcomes.json": varies})).events()
    (unstable,) = [e for e in events if e["type"] == "baseline.unstable"]
    assert (unstable["gate"], unstable["tests"]) == ("existing-tests", [TEST])


def test_the_evidence_has_the_head_of_the_ledger_before_it_was_built() -> None:
    done = audit()
    events = done.events()
    built = next(i for i, e in enumerate(events) if e["type"] == "evidence.built")
    ledger = done.statement()["predicate"]["ledger"]
    assert ledger == {"head": events[built - 1]["hash"], "events": built}
    assert done.audited.evidence is not None
    assert events[built]["digest"] == done.audited.evidence.digest


def test_the_findings_of_the_aggregation_stop_the_run_without_evidence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    states = tuple(
        (state, (*gates, "mystery") if state == "preparing" else gates)
        for state, gates in audit_module.STATES
    )
    monkeypatch.setattr(audit_module, "STATES", states)
    done = audit()
    assert done.audited.verdict is Verdict.ERROR
    assert [f.code for f in done.audited.findings] == ["gate-unknown"]
    assert done.audited.evidence is None
    last = done.events()[-1]
    assert (last["type"], last["verdict"], last["findings"]) == (
        "run.finished",
        "ERROR",
        ["gate-unknown"],
    )
