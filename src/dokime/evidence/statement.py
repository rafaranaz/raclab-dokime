"""The statement of a run (ADR-0023, ADR-0064).

It is the in-toto Statement v1 alone, without the envelope that block E signs, and its bytes are
the canonical form of ADR-0062. The predicate of ADR-0064 is closed: a field the run does not fill
is left out, never written as `null`. `evidence` records the verdicts it is given and decides none.
"""

import hashlib
from collections import Counter
from dataclasses import dataclass

from dokime.core.canonical import canonical
from dokime.core.findings import Finding
from dokime.core.runtime import Digest
from dokime.evidence.run import (
    Contract,
    FailedOrder,
    Gate,
    GateNotReached,
    GateRan,
    Holdout,
    Image,
    Inputs,
    RelationsRecord,
    Run,
)
from dokime.evidence.schema import (
    MESSAGE,
    MOTIVES,
    NAME,
    ORIGINS,
    PREDICATE,
    RELATIONS,
    SEALED,
    STATEMENT,
    cut,
    read_back,
)
from dokime.evidence.unchecked import not_checked

type Value = dict[str, object]


@dataclass(frozen=True)
class Evidence:
    """The evidence of a run: the name of its file, its bytes and their digest."""

    name: str
    data: bytes
    digest: str


def build(run: Run) -> Evidence:
    """Build the evidence of a run, read back against the schema, or refuse the run."""
    _check(run)
    data = canonical(statement(run)).encode("utf-8")
    found = read_back(data)
    if found:
        listed = "; ".join(f"{finding.code}: {finding.message}" for finding in found)
        raise ValueError(f"the evidence of the run does not read back: {listed}")
    return Evidence(
        name=f"{run.story}.statement.json",
        data=data,
        digest="sha256:" + hashlib.sha256(data).hexdigest(),
    )


def statement(run: Run) -> Value:
    """The statement of a run, as a value of the canonical form."""
    predicate: Value = {
        "verdict": run.verdict.value,
        "delivered": False,
        "independence": "self-attested",
        "verifier": _present(
            harness=run.harness,
            ran_on="developer",
            commit=None if run.harness_commit is None else run.harness_commit.text,
        ),
        "contract": _contract(run.story, run.contract),
        "inputs": _inputs(run.inputs),
        "gates": [_gate(gate) for gate in run.gates],
        "human_decisions": [],
        "not_checked": not_checked(run),
        "ledger": _present(head=run.ledger.hash, events=run.ledger.events),
    }
    if run.repeated is not None:
        predicate["repeated"] = {
            "runs": run.repeated.runs,
            "consistent": run.repeated.consistent,
        }
    return {
        "_type": STATEMENT,
        "subject": [
            {"name": "tree", "digest": {"gitTree": run.tree.text}},
            {"name": "change.patch", "digest": {"sha256": hashlib.sha256(run.patch).hexdigest()}},
        ],
        "predicateType": PREDICATE,
        "predicate": predicate,
    }


def _contract(story: str, contract: Contract | None) -> Value:
    return _present(story=story, digest=None if contract is None else _sha256(contract.text))


def _image(image: Image | None) -> Value | None:
    if image is None:
        return None
    return _present(
        digest=image.digest.text,
        platform=None if image.platform is None else image.platform.text,
    )


def _inputs(inputs: Inputs) -> Value:
    return _present(
        base=inputs.base.text,
        policy={
            "digest": inputs.policy.digest(),
            "source": "file" if inputs.policy.from_file else "defaults",
        },
        image=_image(inputs.image),
        pack=None if inputs.pack is None else {"digest": _sha256(inputs.pack)},
        probe=None if inputs.probe is None else inputs.probe.text,
        change_image=_image(inputs.change_image),
    )


def _gate(gate: Gate) -> Value:
    if isinstance(gate, GateRan):
        entry: Value = {
            "gate": gate.gate,
            "status": "run",
            "verdict": gate.verdict.value,
            "findings": [_finding(finding) for finding in gate.findings],
        }
        if gate.checks:
            entry["checks"] = [{"origin": c.origin, "total": c.total} for c in gate.checks]
        if gate.holdout is not None:
            entry["holdout"] = _holdout(gate.holdout)
        if gate.relations is not None:
            entry["relations"] = {
                "seed": gate.relations.seed,
                "failed": [_failed(one) for one in gate.relations.failed],
            }
        return entry
    status = "not-reached" if isinstance(gate, GateNotReached) else "not-applicable"
    return {"gate": gate.gate, "status": status, "reason": gate.reason}


def _holdout(holdout: Holdout) -> Value:
    """The hold-out of the batch: cases, ids of visible examples and the digest, nothing else."""
    return {
        "batch": holdout.batch,
        "held": [{"requirement": c.requirement, "case": c.case} for c in holdout.held],
        "kept_visible": list(holdout.kept_visible),
        "without_holdout": [
            {"requirement": c.requirement, "case": c.case, "motive": c.motive}
            for c in holdout.without_holdout
        ],
    }


def _failed(one: FailedOrder) -> Value:
    entry: Value = {"relation": one.relation, "example": one.example}
    if one.order is not None:
        entry["order"] = list(one.order)
    return entry


def _finding(finding: Finding) -> Value:
    return {
        "code": finding.code,
        "verdict": finding.verdict.value,
        "lines": list(finding.lines),
        "untrusted": [{"label": "message", "text": cut(finding.message, MESSAGE)}],
    }


def _present(**fields: object) -> Value:
    return {name: value for name, value in fields.items() if value is not None}


def _sha256(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _check(run: Run) -> None:
    names = [run.story]
    if run.contract is not None:
        names += [requirement.id for requirement in run.contract.requirements]
    ran = [gate for gate in run.gates if isinstance(gate, GateRan)]
    names += [example for gate in ran for example in gate.unstable_examples]
    for name in names:
        if NAME.fullmatch(name) is None:
            raise ValueError(
                f"the name {name!r} of the story, a requirement or an unstable example is not"
                " letters and digits in words joined by hyphens, starting with a letter"
            )
    _check_records(ran)
    counted = Counter(gate.gate for gate in run.gates)
    repeated = sorted(name for name, count in counted.items() if count > 1)
    if repeated:
        raise ValueError(f"the gate {repeated[0]!r} is listed more than once")
    for gate in ran:
        for checks in gate.checks:
            if checks.origin not in ORIGINS or checks.total < 1:
                raise ValueError(
                    f"the check of origin {checks.origin!r} with total {checks.total} of the gate"
                    f" {gate.gate!r} is not of {', '.join(ORIGINS)} with a total of at least one"
                )


def _check_records(ran: list[GateRan]) -> None:
    """Check the records that a gate may carry: the hold-out and the record of the relations."""
    for gate in ran:
        if gate.holdout is not None:
            _check_holdout(gate.gate, gate.holdout)
        if gate.relations is not None:
            _check_relations(gate.gate, gate.relations)


def _check_holdout(gate: str, holdout: Holdout) -> None:
    if gate != SEALED:
        raise ValueError(f"the gate {gate!r} has a hold-out, which only {SEALED} may have")
    try:
        Digest(holdout.batch)
    except ValueError:
        raise ValueError(f"the digest {holdout.batch!r} of the batch is not a digest") from None
    names = [
        *(name for c in holdout.held for name in (c.requirement, c.case)),
        *holdout.kept_visible,
        *(name for c in holdout.without_holdout for name in (c.requirement, c.case)),
    ]
    for name in names:
        if NAME.fullmatch(name) is None:
            raise ValueError(f"the name {name!r} of the hold-out is not a name")
    for case in holdout.without_holdout:
        if case.motive not in MOTIVES:
            raise ValueError(f"the motive {case.motive!r} is not one of {', '.join(MOTIVES)}")


def _check_relations(gate: str, record: RelationsRecord) -> None:
    if gate != RELATIONS:
        raise ValueError(f"the gate {gate!r} has a record of relations, which only {RELATIONS} may")
    if isinstance(record.seed, bool) or record.seed < 0:
        raise ValueError(f"the seed {record.seed!r} of the relations is not a natural number")
    for one in record.failed:
        for name in (one.relation, one.example):
            if NAME.fullmatch(name) is None:
                raise ValueError(f"the name {name!r} of the record of relations is not a name")
        if one.order is not None and sorted(one.order) != list(range(len(one.order))):
            raise ValueError(
                f"the order {one.order!r} is not the indices from zero of its items, each once"
            )
