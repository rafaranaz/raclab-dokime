# SDD-EARS: INTERFACES-177 INTERFACES-178 INTERFACES-179 INTERFACES-180 INTERFACES-181
import dataclasses
import json
from typing import Any

import pytest

from dokime.core.repository import RefusalError
from dokime.verify.sealed import batch_bytes
from tests.interfaces.audit_runs import CONTRACT, CONTRACT_PATH, ON_CHANGE, Done, audit, change
from tests.interfaces.sealed_audits import (
    BATCH_BASE,
    SEAL,
    SEALED_PATH,
    StoreDouble,
    history,
    sealed_files,
)

HOLDS = change(**{"answers.json": json.dumps({**ON_CHANGE, "E-0003": 6})})
FAILS = change(**{"answers.json": json.dumps({**ON_CHANGE, "E-0003": 9})})


def run(
    files: dict[str, Any] | None = None,
    changed: bytes = HOLDS,
    store: StoreDouble | None = None,
    *,
    keyed: bool = True,
    **request: Any,
) -> tuple[Done, StoreDouble]:
    store = store or StoreDouble()
    done = audit(
        sealed_files() if files is None else files,
        changed,
        sealing=True,
        history=history,
        sealed=store if keyed else None,
        ancestors=(BATCH_BASE,),
        **request,
    )
    return done, store


def sealed_gate(done: Done) -> dict[str, Any]:
    gate: dict[str, Any] = done.gates()[-1]
    assert gate["gate"] == "sealed-examples"
    return gate


def codes(gate: dict[str, Any]) -> list[str]:
    return [f["code"] for f in gate.get("findings", [])]


def test_a_held_out_example_that_fails_on_the_change_fails_the_gate() -> None:
    done, _ = run(changed=FAILS)
    gate = sealed_gate(done)
    assert (gate["verdict"], codes(gate)) == ("FAIL", ["sealed-example-fails"])
    assert done.audited.verdict.value == "FAIL"


def test_without_the_key_the_gate_is_not_applicable_and_nothing_is_opened() -> None:
    done, store = run(keyed=False)
    assert sealed_gate(done) == {
        "gate": "sealed-examples",
        "status": "not-applicable",
        "reason": "the key is not here",
    }
    assert store.opened == []


@pytest.mark.parametrize("keyed", [True, False])
def test_a_contract_never_sealed_is_not_applicable_for_its_own_reason(keyed: bool) -> None:
    files = sealed_files(**{CONTRACT_PATH.replace("/", "__"): CONTRACT})
    files.pop(SEALED_PATH)
    done, store = run(files, keyed=keyed)
    gate = sealed_gate(done)
    assert (gate["status"], gate["reason"]) == (
        "not-applicable",
        "the contract holds out no example",
    )
    assert store.opened == []


@pytest.mark.parametrize("keyed", [True, False])
def test_held_out_entries_without_their_batch_are_an_error_with_or_without_the_key(
    keyed: bool,
) -> None:
    files = sealed_files()
    files.pop(SEALED_PATH)
    done, store = run(files, keyed=keyed)
    gate = sealed_gate(done)
    assert (gate["verdict"], codes(gate)) == ("ERROR", ["sealed-batch-missing"])
    assert store.opened == []


@pytest.mark.parametrize("keyed", [True, False])
def test_a_batch_that_the_contract_does_not_name_is_an_error_with_or_without_the_key(
    keyed: bool,
) -> None:
    files = sealed_files(**{CONTRACT_PATH.replace("/", "__"): CONTRACT})
    done, store = run(files, keyed=keyed)
    gate = sealed_gate(done)
    assert (gate["verdict"], codes(gate)) == ("ERROR", ["sealed-batch-mismatch"])
    assert store.opened == []


def test_a_passphrase_that_does_not_open_the_identity_is_an_error_of_the_gate() -> None:
    refused = StoreDouble(refusal=RefusalError("wrong-passphrase", "the passphrase is wrong"))
    done, _ = run(store=refused)
    gate = sealed_gate(done)
    assert (gate["verdict"], codes(gate)) == ("ERROR", ["wrong-passphrase"])
    assert "holdout" not in gate


def test_a_batch_that_does_not_read_is_an_error_of_the_gate() -> None:
    done, _ = run(store=StoreDouble(content=b"not a batch"))
    gate = sealed_gate(done)
    assert (gate["verdict"], codes(gate)) == ("ERROR", ["unreadable-batch"])


def test_the_gate_not_built_opens_nothing() -> None:
    store = StoreDouble()
    done = audit(sealed_files(), HOLDS, history=history, sealed=store, ancestors=(BATCH_BASE,))
    assert sealed_gate(done)["status"] == "not-applicable"
    assert store.opened == []


def test_a_sealed_batch_that_is_a_link_is_an_error_and_nothing_is_opened() -> None:
    files = sealed_files()
    files[SEALED_PATH] = ("->", "elsewhere")
    done, store = run(files)
    gate = sealed_gate(done)
    assert (gate["verdict"], codes(gate)) == ("ERROR", ["file-not-regular"])
    assert store.opened == []


def test_a_gate_that_does_not_observe_records_no_hold_out() -> None:
    other = dataclasses.replace(SEAL.batch, kept_visible=("E-0001",))
    done, _ = run(store=StoreDouble(content=batch_bytes(other)))
    gate = sealed_gate(done)
    assert (gate["verdict"], codes(gate)) == ("ERROR", ["sealed-batch-mismatch"])
    assert "holdout" not in gate
