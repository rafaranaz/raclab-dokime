"""Cases of the corpus with a sealed batch: their audit on a commit of their own, and its judge.

The gate `sealed-examples` reads the contract and the sealed batch of a story from the base, so a
case whose contract has a `sealed.age` is audited on a commit on top of its base that adds both.
Without the key, a case that only the hold-out catches passes what is visible and the gate is not
applicable; with the key, it is judged on its `expected`, as any other.
"""

import subprocess
from pathlib import Path
from typing import Any

import yaml

from tests.corpus.cases import Case

HELD_OUT = "fails-a-held-out-example"
SEALED_GATE = "sealed-examples"
NOT_HERE = "the key is not here"
IDENTITY = "DOKIME_CORPUS_IDENTITY"


def sealed_of(case: Case) -> Path | None:
    """The sealed batch next to the contract of a case, or none."""
    sealed = case.contract.parent / "sealed.age"
    return sealed if sealed.is_file() else None


def story_of(case: Case) -> str:
    """The story of the contract of a case."""
    return str(yaml.safe_load(case.contract.read_text())["story"])


def on_top(checkout: Path, case: Case) -> str:
    """Commit the contract and the batch of a case on top of its base, and give the commit."""
    sealed = sealed_of(case)
    if sealed is None:
        raise ValueError(f"the case {case.key} has no sealed batch")
    changes = checkout / ".dokime" / "changes" / story_of(case)
    changes.mkdir(parents=True, exist_ok=True)
    (changes / "contract.yaml").write_bytes(case.contract.read_bytes())
    (changes / "sealed.age").write_bytes(sealed.read_bytes())
    name = ("-c", "user.name=dokime corpus", "-c", "user.email=corpus@dokime.invalid")
    _git(checkout, "add", "--force", ".dokime")
    _git(checkout, *name, "commit", "--quiet", "--message", f"the sealed contract of {case.key}")
    return _git(checkout, "rev-parse", "HEAD")


def _git(directory: Path, *args: str) -> str:
    done = subprocess.run(
        ["git", "-C", str(directory), *args], capture_output=True, text=True, check=True
    )
    return done.stdout.strip()


def _first_failing(gates: list[dict[str, Any]]) -> str | None:
    return next((g["gate"] for g in gates if g["status"] == "run" and g["verdict"] == "FAIL"), None)


def judge(case: Case, document: dict[str, Any], key: bool) -> list[str]:
    """What is wrong with the audit of a case, given whether the key was there; empty if nothing."""
    gates = document["gates"]
    failing = _first_failing(gates)
    if case.fields.get("label") == HELD_OUT and not key:
        wrong = [] if failing is None else [f"the gate {failing} failed without the key"]
        sealed = [g for g in gates if g["gate"] == SEALED_GATE]
        if sealed != [{"gate": SEALED_GATE, "status": "not-applicable", "reason": NOT_HERE}]:
            wrong.append(f"{SEALED_GATE} is not applicable as the key is not here: {sealed}")
        return wrong
    wrong = []
    if document["verdict"] != case.fields["expected"]:
        wrong.append(f"the verdict is {document['verdict']}, not {case.fields['expected']}")
    if not case.good and failing != case.fields.get("failing_gate"):
        wrong.append(f"the first failing gate is {failing}, not {case.fields.get('failing_gate')}")
    return wrong


def key_arguments(identity: str | None, descriptor: int | None) -> list[str]:
    """The arguments of `audit` that give it the identity and the descriptor of its passphrase."""
    if identity is None:
        return []
    return ["--identity", identity, "--passphrase-fd", str(descriptor)]
