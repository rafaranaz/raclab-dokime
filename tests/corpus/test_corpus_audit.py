# SDD-EARS: CORPUS-050 CORPUS-051 CORPUS-052 CORPUS-053 CORPUS-054 CORPUS-055 CORPUS-070
"""The audit of each case of the corpus with the command `audit`, the real git and podman.

It measures the exit criterion of A3: a good case passes, and a bad one fails first at the gate
that its label names. Each audit writes one line before it is judged, so that the job shows the
measurement of every case, the ones that do not meet it included.
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from dokime.evidence.schema import read_back
from tests.corpus.cases import CASES, Case
from tests.corpus.clones import clone, skip_unless_asked
from tests.corpus.projects import PROJECTS
from tests.sandbox.engines import require


def first_failing(gates: list[dict[str, Any]]) -> str | None:
    """The first gate, in the order of the audit flow, whose verdict is `FAIL`."""
    return next((g["gate"] for g in gates if g["status"] == "run" and g["verdict"] == "FAIL"), None)


@pytest.mark.parametrize("case", CASES, ids=lambda c: c.key)
def test_a_case_gets_its_expected_verdict_at_its_gate(tmp_path: Path, case: Case) -> None:
    skip_unless_asked()
    require("git")
    require("podman")
    (project,) = [p for p in PROJECTS if p.name == case.project]
    checkout = clone(project, tmp_path / "project")
    temporary = tmp_path / "temporary"
    temporary.mkdir()
    out = tmp_path / "out"
    done = subprocess.run(
        [
            sys.executable,
            "-m",
            "dokime.interfaces",
            "audit",
            "--project",
            str(checkout),
            "--base",
            str(case.fields["base"]),
            "--patch",
            str(case.directory / str(case.fields["patch"])),
            "--contract",
            str(case.contract),
            "--pack",
            str(project.pack),
            "--out",
            str(out),
            "--format",
            "json",
        ],
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, "TMPDIR": str(temporary)},
        timeout=3600,
    )
    document = json.loads(done.stdout)
    failing = first_failing(document["gates"])
    expected, gate = case.fields["expected"], case.fields.get("failing_gate")
    print(
        f"case {case.key}: verdict {document['verdict']}, expected {expected};"
        f" first failing gate {failing}, failing_gate {gate}"
    )
    for finding in document["findings"]:
        print(f"  {finding['gate']}: {finding['verdict']} {finding['code']}")
    assert document["verdict"] == expected, done.stdout + done.stderr
    if not case.good:
        assert failing == gate, done.stdout
    if document["evidence"] is not None:
        data = Path(document["evidence"]["path"]).read_bytes()
        assert read_back(data) == ()
        predicate = json.loads(data)["predicate"]
        (sealed,) = [g for g in predicate["gates"] if g["gate"] == "sealed-examples"]
        if sealed["status"] != "not-reached":
            assert (sealed["status"], sealed["reason"]) == (
                "not-applicable",
                "the contract holds out no example",
            )
        ran = any(g["gate"] == "repeatability" and g["status"] == "run" for g in predicate["gates"])
        if ran:
            assert predicate.get("repeated") == {"runs": 2, "consistent": True}
        else:
            assert "repeated" not in predicate
