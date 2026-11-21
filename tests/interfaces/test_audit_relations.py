# SDD-EARS: INTERFACES-187 INTERFACES-188 INTERFACES-189
import json
from typing import Any

from tests.interfaces.audit_runs import (
    CONTRACT,
    CONTRACT_PATH,
    ON_BASE,
    ON_CHANGE,
    Done,
    audit,
    base_files,
    change,
)
from tests.interfaces.test_audit_images import RefusesTheBuildsOfTheChange

LISTS = """\
  - id: E-0003
    requirement: add-one
    case: lists
    boundary: function
    target: p:g
    origin: human
    steps:
      - input: {args: [[3, 1, 2]]}
        expect: {returns: [1, 2, 3]}

relations:
  - id: L1
    requirement: add-one
    relation: idempotent
    target: p:f
  - id: L2
    requirement: add-one
    relation: order-insensitive
    target: p:g
    over: args[0]
"""
SEED = 20261122


def related(policy: bytes | None = None) -> dict[str, Any]:
    files: dict[str, Any] = {
        CONTRACT_PATH.replace("/", "__"): CONTRACT + LISTS.encode(),
        "answers.json": json.dumps({**ON_BASE, "E-0003": [3, 1, 2]}).encode(),
    }
    if policy is not None:
        files[".dokime__policy.yaml"] = policy
    return base_files(**files)


def answered(follow_ups: dict[str, object]) -> bytes:
    return change(**{"answers.json": json.dumps({**ON_CHANGE, "E-0003": [1, 2, 3], **follow_ups})})


HOLDING = {"L1/E-0001/0": 2, **{f"L2/E-0003/{n}": [1, 2, 3] for n in range(1, 12)}}
"""The answers of the follow-ups, numbered across the gate: L1 takes 0, L2 the next ones."""


def gate_of(done: Done) -> dict[str, Any]:
    (gate,) = [g for g in done.gates() if g["gate"] == "relations"]
    found: dict[str, Any] = gate
    return found


def test_the_gate_records_its_seed_when_it_starts() -> None:
    done = audit(related(), answered(HOLDING), relating=True, relations_seed=SEED)
    started = [e for e in done.events() if e["type"] == "gate.started" and e["gate"] == "relations"]
    assert [e["seed"] for e in started] == [SEED] * len(started)
    assert started


def test_the_gate_runs_on_the_seed_of_the_audit_and_the_permutations_of_the_policy() -> None:
    policy = b"format: 1\nrelations:\n  permutations: 1\n"
    done = audit(related(policy), answered(HOLDING), relating=True, relations_seed=SEED)
    gate = gate_of(done)
    assert (gate["status"], gate["verdict"]) == ("run", "PASS")
    assert gate["checks"] == [{"origin": "derived", "total": 3}]
    assert gate["relations"] == {"seed": SEED, "failed": []}


def test_the_evidence_gets_the_follow_ups_that_failed_with_their_orders() -> None:
    failing = {**HOLDING, "L1/E-0001/0": 3, "L2/E-0003/1": [3, 2, 1]}
    done = audit(related(), answered(failing), relating=True, relations_seed=SEED)
    gate = gate_of(done)
    assert gate["verdict"] == "FAIL"
    assert [f["code"] for f in gate["findings"]] == ["relation-fails", "relation-fails"]
    assert gate["relations"]["seed"] == SEED
    assert gate["relations"]["failed"] == [
        {"relation": "L1", "example": "E-0001"},
        {"relation": "L2", "example": "E-0003", "order": [2, 1, 0]},
    ]


def test_the_gate_not_built_runs_nothing() -> None:
    done = audit(related(), answered(HOLDING), relations_seed=SEED)
    gate = gate_of(done)
    assert gate["status"] == "not-applicable"
    asked = [r.example for _, requests in done.observer.calls for r in requests]
    assert not any("/" in name for name in asked)


def test_a_refused_build_of_the_change_is_an_error_of_the_gate_and_nothing_else() -> None:
    done = audit(
        related(),
        answered(HOLDING),
        runtime=RefusesTheBuildsOfTheChange(),
        relating=True,
        relations_seed=SEED,
    )
    gate = gate_of(done)
    assert [(f["code"], f["verdict"]) for f in gate["findings"]] == [("build-failed", "ERROR")]
    assert "relations" not in gate
