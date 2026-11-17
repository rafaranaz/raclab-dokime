# SDD-EARS: CORPUS-045 CORPUS-046 CORPUS-047 CORPUS-048
"""The witnesses that the good cases come from, and the measurement of ADR-0057."""

import re
import subprocess
import tomllib
from pathlib import Path
from typing import Any

import pytest

from dokime.core.repository import CommitName
from tests.corpus.cases import CASES
from tests.corpus.clones import clone, skip_unless_asked
from tests.corpus.projects import PROJECTS
from tests.corpus.witnesses import witness_at
from tests.sandbox.engines import ENGINES, require

HERE = Path(__file__).parent
FIXTURE: dict[str, Any] = tomllib.loads((HERE / "witnesses.toml").read_text())
WITNESSES: list[dict[str, Any]] = FIXTURE["witness"]
ADR = next((HERE.parents[1] / "docs" / "adr").glob("0057-*[!s].md"))
ROW = re.compile(r"\| (?P<name>[a-z-]+) \| (?P<looked>\d+) \| (?P<found>\d+) \|")


@pytest.mark.parametrize("witness", WITNESSES, ids=lambda w: w["case"])
def test_the_commit_of_a_good_case_is_a_witness_with_its_tests(
    tmp_path: Path, witness: dict[str, Any]
) -> None:
    skip_unless_asked()
    require("git")
    require("podman")
    (project,) = [p for p in PROJECTS if p.name == witness["project"]]
    checkout = clone(project, tmp_path / "project")
    (case,) = [c for c in CASES if c.project == project.name and c.name == witness["case"]]
    parent = subprocess.run(
        ["git", "-C", str(checkout), "rev-parse", f"{witness['commit']}^"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    assert parent == case.fields["base"]
    before = ENGINES["podman"].containers()
    candidate = witness_at(project, checkout, CommitName(witness["commit"]))
    assert candidate.witness
    assert sorted(candidate.turned_green) == sorted(witness["turned_green"])
    assert ENGINES["podman"].containers() <= before


def test_every_good_case_names_the_witness_it_comes_from() -> None:
    good = sorted((c.project, c.name) for c in CASES if c.good)
    assert sorted((w["project"], w["case"]) for w in WITNESSES) == good
    assert all(re.fullmatch(r"[0-9a-f]{40}", w["commit"]) for w in WITNESSES)


def test_the_measurement_is_the_table_of_the_basis_of_adr_0057() -> None:
    rows = [(m["name"], int(m["looked"]), int(m["found"])) for m in ROW.finditer(ADR.read_text())]
    fixture = [
        (p["name"], p["looked_at"], p["witnesses"]) for p in FIXTURE["measurement"]["project"]
    ]
    assert fixture == rows
    assert {name for name, _, _ in rows} == {p.name for p in PROJECTS}


def test_no_project_has_more_witnesses_than_candidates_looked_at() -> None:
    for project in FIXTURE["measurement"]["project"]:
        assert 0 <= project["witnesses"] <= project["looked_at"], project["name"]
