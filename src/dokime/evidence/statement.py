"""The statement of a run (ADR-0023, ADR-0064).

It is the in-toto Statement v1 alone, without the envelope that block E signs, and its bytes are
the canonical form of ADR-0062. The predicate of ADR-0064 is closed: a field the run does not fill
is left out, never written as `null`. `evidence` records the verdicts it is given and decides none.
"""

import hashlib
import re
from collections import Counter
from dataclasses import dataclass

from dokime.core.canonical import canonical
from dokime.core.findings import Finding
from dokime.evidence.run import Contract, Gate, GateRan, Inputs, Run
from dokime.evidence.unchecked import not_checked

STATEMENT = "https://in-toto.io/Statement/v1"
PREDICATE = "https://github.com/rafaranaz/raclab-dokime/attestation/conformance/v0.1"
ORIGINS = ("existing", "human", "derived", "model")
"""The origins of the checks of a gate."""
_NAME = re.compile(r"[A-Za-z][A-Za-z0-9]*(-[A-Za-z0-9]+)*")
"""A name, as the story or the id of a requirement or an example."""

type Value = dict[str, object]


@dataclass(frozen=True)
class Evidence:
    """The evidence of a run: the name of its file, its bytes and their digest."""

    name: str
    data: bytes
    digest: str


def build(run: Run) -> Evidence:
    """Build the evidence of a run, or refuse a run that breaks the rules of its fields."""
    _check(run)
    data = canonical(statement(run)).encode("utf-8")
    return Evidence(
        name=f"{run.story}.statement.json",
        data=data,
        digest="sha256:" + hashlib.sha256(data).hexdigest(),
    )


def statement(run: Run) -> Value:
    """The statement of a run, as a value of the canonical form."""
    return {
        "_type": STATEMENT,
        "subject": [
            {"name": "tree", "digest": {"gitTree": run.tree.text}},
            {"name": "change.patch", "digest": {"sha256": hashlib.sha256(run.patch).hexdigest()}},
        ],
        "predicateType": PREDICATE,
        "predicate": {
            "verdict": run.verdict.value,
            "delivered": False,
            "independence": "self-attested",
            "verifier": {"harness": run.harness, "ran_on": "developer"},
            "contract": _contract(run.story, run.contract),
            "inputs": _inputs(run.inputs),
            "gates": [_gate(gate) for gate in run.gates],
            "human_decisions": [],
            "not_checked": not_checked(run),
            "ledger": _present(head=run.ledger.hash, events=run.ledger.events),
        },
    }


def _contract(story: str, contract: Contract | None) -> Value:
    return _present(story=story, digest=None if contract is None else _sha256(contract.text))


def _inputs(inputs: Inputs) -> Value:
    image = inputs.image
    return _present(
        base=inputs.base.text,
        policy={
            "digest": inputs.policy.digest(),
            "source": "file" if inputs.policy.from_file else "defaults",
        },
        image=None
        if image is None
        else _present(
            digest=image.digest.text,
            platform=None if image.platform is None else image.platform.text,
        ),
        pack=None if inputs.pack is None else {"digest": _sha256(inputs.pack)},
        probe=None if inputs.probe is None else inputs.probe.text,
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
        return entry
    return {"gate": gate.gate, "status": "not-applicable", "reason": gate.reason}


def _finding(finding: Finding) -> Value:
    return {
        "code": finding.code,
        "verdict": finding.verdict.value,
        "lines": list(finding.lines),
        "untrusted": [{"label": "message", "text": finding.message}],
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
        if _NAME.fullmatch(name) is None:
            raise ValueError(
                f"the name {name!r} of the story, a requirement or an unstable example is not"
                " letters and digits in words joined by hyphens, starting with a letter"
            )
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
