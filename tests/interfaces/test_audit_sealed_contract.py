# SDD-EARS: INTERFACES-183 INTERFACES-184
from pathlib import Path

from tests.interfaces.audit_runs import CONTRACT, STORY, base_files
from tests.interfaces.sealed_audits import SEAL, WHOLE
from tests.interfaces.test_audit_sealed import codes, run, sealed_gate


def given(tmp_path: Path, text: str) -> Path:
    path = tmp_path / STORY / "contract.yaml"
    path.parent.mkdir(parents=True)
    path.write_text(text)
    return path


def test_the_visible_contract_given_from_outside_runs_the_gate(tmp_path: Path) -> None:
    done, store = run(story=None, contract=given(tmp_path, SEAL.visible))
    gate = sealed_gate(done)
    assert (gate["status"], gate["verdict"]) == ("run", "PASS")
    assert len(store.opened) == 1


def test_the_whole_contract_given_from_outside_is_a_mismatch_that_says_why(
    tmp_path: Path,
) -> None:
    done, store = run(story=None, contract=given(tmp_path, WHOLE))
    gate = sealed_gate(done)
    assert (gate["verdict"], codes(gate)) == ("ERROR", ["sealed-batch-mismatch"])
    (finding,) = gate["findings"]
    said = finding["untrusted"][0]["text"]
    assert "lacks the entries held_out of the base" in said
    assert "visible contract" in said
    assert store.opened == []


def test_a_contract_given_with_other_entries_held_out_is_a_mismatch(tmp_path: Path) -> None:
    other = SEAL.visible.replace(SEAL.visible.split("digest: ")[1].strip(), "sha256:" + "0" * 64)
    done, store = run(story=None, contract=given(tmp_path, other))
    gate = sealed_gate(done)
    assert (gate["verdict"], codes(gate)) == ("ERROR", ["sealed-batch-mismatch"])
    assert store.opened == []


def test_a_contract_never_sealed_given_from_outside_on_a_base_never_sealed(tmp_path: Path) -> None:
    done, store = run(base_files(), story=None, contract=given(tmp_path, CONTRACT.decode()))
    gate = sealed_gate(done)
    assert (gate["status"], gate["reason"]) == (
        "not-applicable",
        "the contract holds out no example",
    )
    assert store.opened == []
