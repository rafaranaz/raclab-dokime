# SDD-EARS: INTERFACES-128 INTERFACES-129 INTERFACES-130
import json
from pathlib import Path

import pytest

from dokime.core.findings import Finding
from dokime.core.verdicts import Verdict
from dokime.evidence.run import GateNotApplicable, GateNotReached, GateRan
from dokime.evidence.statement import Evidence
from dokime.interfaces.audit import Audited
from dokime.interfaces.audit_command import json_of, text_of
from dokime.interfaces.cli import main

FAILS = Finding(code="example-fails", message="it fails", verdict=Verdict.FAIL, lines=(12, 14))
TOUCHED = Finding(code="protected-path", message="tests changed", verdict=Verdict.FAIL)
AUDITED = Audited(
    verdict=Verdict.FAIL,
    gates=(
        GateRan("contract", Verdict.PASS),
        GateRan("protected-paths", Verdict.FAIL, findings=(TOUCHED,)),
        GateRan("visible-examples", Verdict.FAIL, findings=(FAILS,)),
        GateNotApplicable("relations", "the gate is built in block B"),
        GateNotReached("sealed-examples", "the run stopped"),
    ),
    evidence=Evidence(name="s.statement.json", data=b"{}", digest="sha256:" + "d" * 64),
)
EVIDENCE = Path("/out/s.statement.json")


def test_the_text_lists_the_gates_the_findings_the_evidence_and_the_verdict() -> None:
    assert text_of(AUDITED, EVIDENCE).splitlines() == [
        "gate contract: run PASS",
        "gate protected-paths: run FAIL",
        "gate visible-examples: run FAIL",
        "gate relations: not-applicable: the gate is built in block B",
        "gate sealed-examples: not-reached: the run stopped",
        "protected-paths: FAIL protected-path: tests changed",
        "visible-examples: FAIL example-fails: it fails (lines 12, 14)",
        f"evidence /out/s.statement.json sha256:{'d' * 64}",
        "FAIL: 2 findings (2 fail)",
    ]


def test_an_audit_without_evidence_has_no_line_of_evidence() -> None:
    ended = Audited(
        verdict=Verdict.ERROR,
        findings=(Finding(code="patch-does-not-apply", message="no", verdict=Verdict.ERROR),),
    )
    assert text_of(ended, None).splitlines() == [
        "audit: ERROR patch-does-not-apply: no",
        "ERROR: 1 finding (1 error)",
    ]


def test_the_json_has_the_verdict_the_evidence_the_ledger_the_gates_and_the_findings() -> None:
    document = json.loads(json_of(AUDITED, EVIDENCE, Path("/out/ledger.jsonl")))
    assert document["verdict"] == "FAIL"
    assert document["evidence"] == {"path": str(EVIDENCE), "digest": "sha256:" + "d" * 64}
    assert document["ledger"] == "/out/ledger.jsonl"
    assert [g["gate"] for g in document["gates"]][:3] == [
        "contract",
        "protected-paths",
        "visible-examples",
    ]
    assert document["gates"][3] == {
        "gate": "relations",
        "status": "not-applicable",
        "reason": "the gate is built in block B",
    }
    assert document["findings"][1] == {
        "gate": "visible-examples",
        "code": "example-fails",
        "verdict": "FAIL",
        "message": "it fails",
        "lines": [12, 14],
    }
    ended = json.loads(json_of(Audited(verdict=Verdict.ERROR), None, Path("/out/ledger.jsonl")))
    assert ended["evidence"] is None


def test_a_refusal_before_the_audit_exits_with_the_code_of_error(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    patch = tmp_path / "p"
    patch.write_text("x")
    code = main(
        [
            "audit",
            "--base",
            "nope",
            "--patch",
            str(patch),
            "--story",
            "s",
            "--out",
            str(tmp_path / "o"),
        ]
    )
    assert code == 2
    capsys.readouterr()
