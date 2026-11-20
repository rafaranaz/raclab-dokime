# SDD-EARS: INTERFACES-182 INTERFACES-180
import hashlib

from tests.interfaces.sealed_audits import SEALED_BYTES
from tests.interfaces.test_audit_sealed import codes, run, sealed_gate


def test_a_sealed_contract_with_the_key_runs_the_gate_and_records_the_hold_out() -> None:
    done, store = run()
    gate = sealed_gate(done)
    assert (gate["status"], gate["verdict"], codes(gate)) == ("run", "PASS", [])
    assert store.opened == [SEALED_BYTES]
    assert gate["holdout"] == {
        "batch": "sha256:" + hashlib.sha256(SEALED_BYTES).hexdigest(),
        "held": [{"requirement": "add-one", "case": "normal"}],
        "kept_visible": [],
        "without_holdout": [
            {"requirement": "keep-zero", "case": "zero", "motive": "single-example"}
        ],
    }
    listed = [e["code"] for e in done.statement()["predicate"]["not_checked"]]
    assert "case-without-holdout" in listed
    assert "best-effort-secrecy" in listed
