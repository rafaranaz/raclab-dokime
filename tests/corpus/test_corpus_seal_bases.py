# SDD-EARS: CORPUS-092 CORPUS-094 CORPUS-095
"""The commit of the recipients that a contract of the corpus is sealed on, made again."""

import json
import os
import re
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import Any

from dokime.platform.sealed_store import create_identity
from tests.corpus.cases import ACTIVE, CASES, Case
from tests.corpus.clones import clone, skip_unless_asked
from tests.corpus.projects import PROJECTS
from tests.corpus.sealing import (
    SEAL_BASES,
    SealBase,
    contract_key,
    make_again,
    on_top,
    seal_bases,
    sealed_of,
)
from tests.sandbox.engines import require

HAND = Path(__file__).parent / "holdout-by-hand"
NAME = "replace-keeps-the-constructor-error"
PASSPHRASE = "a passphrase made for this test only"  # noqa: S105 - of a test identity, made here
AUTHOR, EMAIL = "dokime corpus", "corpus@dokime.invalid"
MESSAGE = "the recipients of the corpus"


def git(directory: Path, *args: str, env: dict[str, str] | None = None) -> str:
    done = subprocess.run(
        ["git", "-C", str(directory), "-c", "commit.gpgsign=false", *args],
        capture_output=True,
        text=True,
        check=True,
        env={**os.environ, **(env or {})},
    )
    return done.stdout.strip()


def recipients_commit(checkout: Path, base: str, recipients: str) -> SealBase:
    """A commit of the recipients on top of a base, by the convention of the corpus: the date of
    the base, a fixed author and a fixed message."""
    git(checkout, "checkout", "--quiet", "--detach", base)
    date = git(checkout, "log", "-1", "--format=%cd", "--date=raw", base)
    target = checkout / ".dokime" / "recipients.txt"
    target.parent.mkdir(exist_ok=True)
    target.write_text(recipients)
    git(checkout, "add", "--force", ".dokime/recipients.txt")
    who = {"GIT_AUTHOR_NAME": AUTHOR, "GIT_AUTHOR_EMAIL": EMAIL, "GIT_AUTHOR_DATE": date}
    who |= {"GIT_COMMITTER_NAME": AUTHOR, "GIT_COMMITTER_EMAIL": EMAIL, "GIT_COMMITTER_DATE": date}
    git(checkout, "commit", "--quiet", "--message", MESSAGE, env=who)
    commit = git(checkout, "rev-parse", "HEAD")
    return SealBase(base, recipients, AUTHOR, EMAIL, date, MESSAGE, commit)


def seal(checkout: Path, contract: Path, out: Path) -> dict[str, Any]:
    """Seal a contract in a checkout, and give the event of its ledger that starts the run."""
    confirm, answer = os.pipe()
    os.write(answer, b"y\n")
    os.close(answer)
    try:
        sealing = subprocess.run(
            [
                sys.executable,
                "-m",
                "dokime.interfaces",
                "contract",
                "seal",
                "--story",
                NAME,
                "--contract",
                str(contract),
                "--out",
                str(out),
                "--project",
                str(checkout),
                "--recipients-confirmed-by-fd",
                str(confirm),
            ],
            capture_output=True,
            text=True,
            check=False,
            pass_fds=(confirm,),
            timeout=600,
        )
    finally:
        os.close(confirm)
    assert sealing.returncode == 0, sealing.stdout + sealing.stderr
    events = [json.loads(line) for line in (out / "ledger.jsonl").read_text().splitlines()]
    (started,) = [e for e in events if e["type"] == "run.started"]
    event: dict[str, Any] = started
    return event


def a_sealed_case(tmp_path: Path, checkout: Path, base: str) -> Case:
    """A good case whose contract and batch are those that the seal wrote in the checkout."""
    directory = tmp_path / "cases" / NAME
    directory.mkdir(parents=True)
    written = checkout / ".dokime" / "changes" / NAME
    for name in ("contract.yaml", "sealed.age"):
        (directory / name).write_bytes((written / name).read_bytes())
    (directory / "patch.diff").write_bytes((HAND / "patches" / f"{NAME}.minimal.diff").read_bytes())
    fields = {
        "project": "python-semver",
        "base": base,
        "contract": "contract.yaml",
        "patch": "patch.diff",
        "label": "good",
        "expected": "PASS",
    }
    (directory / "case.toml").write_text("".join(f'{k} = "{v}"\n' for k, v in fields.items()))
    return Case("python-semver", NAME, directory)


def test_a_contract_sealed_on_a_commit_of_the_recipients_runs_its_held_out_examples(
    tmp_path: Path, data_home: Path
) -> None:
    skip_unless_asked()
    require("git")
    require("podman")
    (project,) = [p for p in PROJECTS if p.name == "python-semver"]
    (source,) = [c for c in CASES if c.key == f"python-semver/{NAME}"]
    base = str(source.fields["base"])
    checkout = clone(project, tmp_path / "project")
    identity = tmp_path / "keys" / "identity.age"
    recipient = create_identity(identity, PASSPHRASE)
    made = recipients_commit(checkout, base, f"{recipient}\n")
    whole = tmp_path / "approved" / "contract.yaml"
    whole.parent.mkdir()
    whole.write_bytes((HAND / "python-semver" / NAME / "contract.yaml").read_bytes())
    started = seal(checkout, whole, tmp_path / "seal")
    assert started["base"] == made.commit
    case = a_sealed_case(tmp_path, checkout, base)
    git(checkout, "clean", "--quiet", "-d", "--force", "-x")
    git(checkout, "checkout", "--quiet", "--detach", base)
    top = on_top(checkout, case, made)
    secret, write = os.pipe()
    os.write(write, f"{PASSPHRASE}\n".encode())
    os.close(write)
    try:
        done = subprocess.run(
            [
                sys.executable,
                "-m",
                "dokime.interfaces",
                "audit",
                "--project",
                str(checkout),
                "--base",
                top,
                "--patch",
                str(case.directory / "patch.diff"),
                "--story",
                NAME,
                "--pack",
                str(project.pack),
                "--out",
                str(tmp_path / "out"),
                "--format",
                "json",
                "--identity",
                str(identity),
                "--passphrase-fd",
                str(secret),
            ],
            capture_output=True,
            text=True,
            check=False,
            pass_fds=(secret,),
            env={**os.environ, "XDG_DATA_HOME": str(data_home)},
            timeout=3600,
        )
    finally:
        os.close(secret)
    document = json.loads(done.stdout)
    (gate,) = [g for g in document["gates"] if g["gate"] == "sealed-examples"]
    found = [f for f in document["findings"] if f["gate"] == "sealed-examples"]
    print(f"sealed on a commit of the recipients: verdict {document['verdict']}, {gate}, {found}")
    assert (gate["status"], gate.get("verdict")) == ("run", "PASS"), (gate, found)
    assert found == []


ENTRIES: list[dict[str, Any]] = tomllib.loads(SEAL_BASES.read_text())["seal"]


def test_each_contract_with_a_sealed_batch_has_the_commit_it_was_sealed_on() -> None:
    sealed = {contract_key(c) for c in ACTIVE if sealed_of(c) is not None}
    assert sorted(e["contract"] for e in ENTRIES) == sorted(sealed)
    for entry in ENTRIES:
        assert re.fullmatch(r"[0-9a-f]{40}", entry["base"]), entry["contract"]
        assert re.fullmatch(r"[0-9a-f]{40}", entry["commit"]), entry["contract"]
        assert re.fullmatch(r"age1[0-9a-z]+\n", entry["recipients"]), entry["contract"]
        assert re.fullmatch(r"\d+ [+-]\d{4}", entry["date"]), entry["contract"]
        assert entry["author"].strip(), entry["contract"]
        assert entry["email"].strip(), entry["contract"]
        assert entry["message"].strip(), entry["contract"]
        assert entry["event"] == "run.started", entry["contract"]
        assert re.fullmatch(r"sha256:[0-9a-f]{64}", entry["event_hash"]), entry["contract"]
        assert entry["event_at"].strip(), entry["contract"]


def test_the_base_of_each_commit_of_the_recipients_is_the_base_of_its_cases() -> None:
    bases = seal_bases()
    for case in ACTIVE:
        if sealed_of(case) is not None:
            assert bases[contract_key(case)].base == case.fields["base"], case.key


def test_each_commit_of_the_recipients_is_made_again_with_its_hash(tmp_path: Path) -> None:
    skip_unless_asked()
    require("git")
    for key, entry in seal_bases().items():
        (project,) = [p for p in PROJECTS if p.name == key.split("/", 1)[0]]
        checkout = clone(project, tmp_path / key)
        assert make_again(checkout, entry, key) == entry.commit
