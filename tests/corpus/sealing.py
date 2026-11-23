"""Cases of the corpus with a sealed batch: their audit on a commit of their own, and its judge.

The gate `sealed-examples` reads the contract and the sealed batch of a story from the base, so a
case whose contract has a `sealed.age` is audited on a commit on top of its base that adds both.
Without the key, a case that only the hold-out catches passes what is visible and the gate is not
applicable; with the key, it is judged on its `expected`, as any other.
"""

import os
import subprocess
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from tests.corpus.cases import Case

HELD_OUT = "fails-a-held-out-example"
SEALED_GATE = "sealed-examples"
NOT_HERE = "the key is not here"
IDENTITY = "DOKIME_CORPUS_IDENTITY"
SEAL_BASES = Path(__file__).parent / "seal-bases.toml"
RECIPIENTS = ".dokime/recipients.txt"


@dataclass(frozen=True)
class SealBase:
    """The commit of the recipients that a contract was sealed on, on top of the base of a case."""

    base: str
    recipients: str
    author: str
    email: str
    date: str
    message: str
    commit: str


class SealBaseMismatchError(Exception):
    """The commit of the recipients made again is not the one that the contract was sealed on."""


def seal_bases() -> dict[str, SealBase]:
    """The commits of the recipients of the contracts of the corpus, by the key of the contract."""
    entries = tomllib.loads(SEAL_BASES.read_text())["seal"]
    fields = SealBase.__dataclass_fields__
    return {e["contract"]: SealBase(**{k: e[k] for k in fields}) for e in entries}


def contract_key(case: Case) -> str:
    """The key of the contract of a case: its project and the directory of the contract."""
    return f"{case.project}/{case.contract.parent.name}"


def recipients_commit(checkout: Path, seal: SealBase) -> str:
    """Make the commit of the recipients on its base in a checkout, and give its hash."""
    _git(checkout, "checkout", "--quiet", "--detach", seal.base)
    target = checkout / RECIPIENTS
    target.parent.mkdir(exist_ok=True)
    target.write_bytes(seal.recipients.encode())
    _git(checkout, "add", "--force", RECIPIENTS)
    who = {"GIT_AUTHOR_NAME": seal.author, "GIT_AUTHOR_EMAIL": seal.email}
    who |= {"GIT_COMMITTER_NAME": seal.author, "GIT_COMMITTER_EMAIL": seal.email}
    who |= {"GIT_AUTHOR_DATE": seal.date, "GIT_COMMITTER_DATE": seal.date}
    commit = ["commit", "--quiet", "--no-verify", "--message", seal.message]
    subprocess.run(
        ["git", "-C", str(checkout), "-c", "commit.gpgsign=false", *commit],
        capture_output=True,
        text=True,
        check=True,
        env={**os.environ, **who},
    )
    return _git(checkout, "rev-parse", "HEAD")


def make_again(checkout: Path, seal: SealBase, contract: str) -> str:
    """Make the commit of the recipients of a contract again, and stop unless it has its hash."""
    made = recipients_commit(checkout, seal)
    if made != seal.commit:
        raise SealBaseMismatchError(
            f"the commit of the recipients of the contract {contract}, made again, is {made},"
            f" not {seal.commit} that the contract was sealed on"
        )
    return made


def sealed_of(case: Case) -> Path | None:
    """The sealed batch next to the contract of a case, or none."""
    sealed = case.contract.parent / "sealed.age"
    return sealed if sealed.is_file() else None


def story_of(case: Case) -> str:
    """The story of the contract of a case."""
    return str(yaml.safe_load(case.contract.read_text())["story"])


def on_top(checkout: Path, case: Case, seal: SealBase | None = None) -> str:
    """Make again the commit of the recipients that the contract of a case was sealed on, commit
    the contract and the batch on top of it, and give the commit."""
    sealed = sealed_of(case)
    if sealed is None:
        raise ValueError(f"the case {case.key} has no sealed batch")
    key = contract_key(case)
    make_again(checkout, seal_bases()[key] if seal is None else seal, key)
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
