# SDD-EARS: CORPUS-050 CORPUS-051 CORPUS-052 CORPUS-053 CORPUS-054 CORPUS-055 CORPUS-070 CORPUS-084
"""The audit of each case of the corpus with the command `audit`, the real git and podman.

It measures the exit criterion of A3: a good case passes, and a bad one fails first at the gate
that its label names. Each audit writes one line before it is judged, so that the job shows the
measurement of every case, the ones that do not meet it included.
"""

import getpass
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from dokime.evidence.schema import read_back
from tests.corpus.cases import RUNNABLE, Case
from tests.corpus.clones import clone, skip_unless_asked
from tests.corpus.projects import PROJECTS
from tests.corpus.results import RESULTS, append, result_line, this_commit
from tests.corpus.sealing import (
    IDENTITY,
    NOT_HERE,
    judge,
    key_arguments,
    on_top,
    sealed_of,
    story_of,
)
from tests.sandbox.engines import require

_PASSPHRASE: list[bytes] = []


def passphrase() -> bytes:
    """The passphrase of the identity, asked once in the terminal for the whole run."""
    if not _PASSPHRASE:
        _PASSPHRASE.append(getpass.getpass("passphrase of the identity of the corpus: ").encode())
    return _PASSPHRASE[0]


def first_failing(gates: list[dict[str, Any]]) -> str | None:
    """The first gate, in the order of the audit flow, whose verdict is `FAIL`."""
    return next((g["gate"] for g in gates if g["status"] == "run" and g["verdict"] == "FAIL"), None)


@pytest.mark.parametrize("case", RUNNABLE, ids=lambda c: c.key)
def test_a_case_gets_its_expected_verdict_at_its_gate(
    tmp_path: Path, data_home: Path, case: Case
) -> None:
    skip_unless_asked()
    require("git")
    require("podman")
    (project,) = [p for p in PROJECTS if p.name == case.project]
    checkout = clone(project, tmp_path / "project")
    temporary = tmp_path / "temporary"
    temporary.mkdir()
    out = tmp_path / "out"
    sealed = sealed_of(case) is not None
    identity = os.environ.get(IDENTITY) if sealed else None
    if sealed:
        subprocess.run(
            ["git", "-C", str(checkout), "checkout", "--quiet", str(case.fields["base"])],
            check=True,
        )
        base, which = on_top(checkout, case), ["--story", story_of(case)]
    else:
        base, which = str(case.fields["base"]), ["--contract", str(case.contract)]
    reading, writing = os.pipe() if identity else (None, None)
    if writing is not None:
        os.write(writing, passphrase() + b"\n")
        os.close(writing)
    done = subprocess.run(
        [
            sys.executable,
            "-m",
            "dokime.interfaces",
            "audit",
            "--project",
            str(checkout),
            "--base",
            base,
            "--patch",
            str(case.directory / str(case.fields["patch"])),
            *which,
            "--pack",
            str(project.pack),
            "--out",
            str(out),
            "--format",
            "json",
            *key_arguments(identity, reading),
        ],
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, "TMPDIR": str(temporary), "XDG_DATA_HOME": str(data_home)},
        pass_fds=() if reading is None else (reading,),
        timeout=3600,
    )
    if reading is not None:
        os.close(reading)
    document = json.loads(done.stdout)
    failing = first_failing(document["gates"])
    expected, gate = case.fields["expected"], case.fields.get("failing_gate")
    print(
        f"case {case.key}: verdict {document['verdict']}, expected {expected};"
        f" first failing gate {failing}, failing_gate {gate};"
        f" key {'given' if identity else 'not given'}"
    )
    for finding in document["findings"]:
        print(f"  {finding['gate']}: {finding['verdict']} {finding['code']}")
    results = os.environ.get(RESULTS)
    if results:
        line = result_line(this_commit(), case.key, document["verdict"], failing, bool(identity))
        append(Path(results), line)
    wrong = judge(case, document, key=identity is not None)
    assert wrong == [], (wrong, done.stdout + done.stderr)
    if document["evidence"] is not None:
        data = Path(document["evidence"]["path"]).read_bytes()
        assert read_back(data) == ()
        predicate = json.loads(data)["predicate"]
        (seen,) = [g for g in predicate["gates"] if g["gate"] == "sealed-examples"]
        if seen["status"] != "not-reached" and not identity:
            reason = NOT_HERE if sealed else "the contract holds out no example"
            assert (seen["status"], seen["reason"]) == ("not-applicable", reason)
        ran = any(g["gate"] == "repeatability" and g["status"] == "run" for g in predicate["gates"])
        if ran:
            assert predicate.get("repeated") == {"runs": 2, "consistent": True}
        else:
            assert "repeated" not in predicate
