# SDD-EARS: CORPUS-045 CORPUS-046 CORPUS-047 CORPUS-048 CORPUS-056 CORPUS-057 CORPUS-058 CORPUS-059
"""The witnesses that the good cases come from, and the measurement of ADR-0057 with its sample."""

import random
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
LABELS: list[dict[str, Any]] = FIXTURE.get("label", [])
SAMPLE: dict[str, Any] = FIXTURE.get("sample", {})
BOUNDARIES = {"function", "cli"}


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


def test_the_table_counts_the_witnesses_the_fixture_classifies() -> None:
    table = {p["name"]: p["witnesses"] for p in FIXTURE["measurement"]["project"]}
    assert set(table) == {p.name for p in PROJECTS}
    for name, witnesses in table.items():
        assert sum(label["project"] == name for label in LABELS) == witnesses, name


def test_no_project_has_more_witnesses_than_candidates_looked_at() -> None:
    for project in FIXTURE["measurement"]["project"]:
        assert 0 <= project["witnesses"] <= project["looked_at"], project["name"]


@pytest.mark.parametrize("label", LABELS, ids=lambda label: label["commit"][:12])
def test_each_witness_has_both_filters_with_their_reasons(label: dict[str, Any]) -> None:
    assert re.fullmatch(r"[0-9a-f]{40}", label["commit"])
    assert isinstance(label["isolated"], bool)
    assert isinstance(label["expressible"], bool)
    assert label["isolated_reason"].strip()
    assert label["expressible_reason"].strip()
    if label["expressible"]:
        assert label["boundary"] in BOUNDARIES
        assert label["target"].strip()
    else:
        assert label["boundary"] == "none"
        assert label["target"] == ""


def test_the_fixture_classifies_some_witnesses() -> None:
    assert LABELS


def test_each_witness_is_classified_once() -> None:
    commits = [(label["project"], label["commit"]) for label in LABELS]
    assert len(commits) == len(set(commits))


def fits_calls_on_an_object() -> set[tuple[str, str]]:
    """The witnesses that the reading of the boundary of B3c gives as fitting option a."""
    draw = tomllib.loads((HERE / "blind" / "draw.toml").read_text())
    result = tomllib.loads((HERE / "boundary" / "result.toml").read_text())
    fits = set(result["option"]["a"]["fits"])
    return {(w["project"], w["commit"]) for w in draw["witness"] if w["id"] in fits}


def test_the_witness_of_each_good_case_is_isolated_and_expressible() -> None:
    labels = {(label["project"], label["commit"]): label for label in LABELS}
    calls = fits_calls_on_an_object()
    for witness in WITNESSES:
        key = (witness["project"], witness["commit"])
        label = labels.get(key)
        assert label is not None, witness["case"]
        assert label["isolated"], witness["case"]
        assert label["expressible"] or key in calls, witness["case"]


def _drawn(seed: int) -> list[tuple[str, str]]:
    """The sample that a seed draws, project by project in the order of the fixture."""
    chance = random.Random(seed)  # noqa: S311 - a draw anyone can repeat, not a secret
    order = list(dict.fromkeys(label["project"] for label in LABELS))
    drawn: list[tuple[str, str]] = []
    for project in order:
        for expressible in (True, False):
            pool = [
                label["commit"]
                for label in LABELS
                if label["project"] == project and label["expressible"] is expressible
            ]
            if pool:
                drawn.append((project, chance.choice(pool)))
    return drawn


def test_the_sample_is_the_one_its_seed_draws() -> None:
    runs = SAMPLE.get("run", [])
    assert runs
    assert [(run["project"], run["commit"]) for run in runs] == _drawn(SAMPLE["seed"])


def test_each_witness_of_the_sample_has_its_run() -> None:
    labels = {(label["project"], label["commit"]): label for label in LABELS}
    for run in SAMPLE.get("run", []):
        label = labels[(run["project"], run["commit"])]
        assert run["example"].strip(), run["commit"]
        assert run["before"].strip(), run["commit"]
        assert run["after"].strip(), run["commit"]
        assert isinstance(run["confirmed"], bool), run["commit"]
        if not label["expressible"]:
            assert run["why_not"].strip(), run["commit"]
