# SDD-EARS: CORPUS-062 CORPUS-063 CORPUS-064 CORPUS-065
"""The hold-out by hand of B0: extended contracts, a split with a seed, and patches of agents."""

import json
import os
import random
import re
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import Any

import pytest
import yaml

from tests.corpus.cases import CASES
from tests.corpus.clones import clone, skip_unless_asked
from tests.corpus.projects import PROJECTS
from tests.sandbox.engines import require

HERE = Path(__file__).parent / "holdout-by-hand"
FIXTURE: dict[str, Any] = (
    tomllib.loads((HERE / "holdout.toml").read_text()) if (HERE / "holdout.toml").exists() else {}
)
CONTRACTS: list[dict[str, Any]] = FIXTURE.get("contract", [])
PATCHES: list[dict[str, Any]] = FIXTURE.get("patch", [])
EXAMPLE = re.compile(r"(?m)^(?=  - id: E-)")


def contract_path(contract: dict[str, Any]) -> Path:
    return HERE / str(contract["project"]) / str(contract["name"]) / "contract.yaml"


def change_cases(contract: dict[str, Any]) -> dict[tuple[str, str], list[str]]:
    """The ids of the examples of each case of a requirement of change, in the order of the file."""
    data = yaml.safe_load(contract_path(contract).read_text())
    change = {r["id"] for r in data["requirements"] if r["kind"] in ("change", "new")}
    cases: dict[tuple[str, str], list[str]] = {}
    for example in data["examples"]:
        if example["requirement"] in change:
            cases.setdefault((example["requirement"], example["case"]), []).append(example["id"])
    return cases


def visible(contract: dict[str, Any]) -> str:
    """The contract without its held-out examples."""
    blocks = EXAMPLE.split(contract_path(contract).read_text())
    held = {f"  - id: {example}\n" for example in contract["held_out"]}
    return "".join(b for b in blocks if not any(b.startswith(h) for h in held))


def test_the_fixture_has_the_three_contracts() -> None:
    assert [c["name"] for c in CONTRACTS] == [
        "format-a-blank-paragraph-between-blocks",
        "nextver-bumps-build-only-versions",
        "replace-keeps-the-constructor-error",
    ]


@pytest.mark.parametrize("contract", CONTRACTS, ids=lambda c: c["name"])
def test_each_case_of_change_has_two_examples_or_more(contract: dict[str, Any]) -> None:
    cases = change_cases(contract)
    assert cases
    assert all(len(ids) >= 2 for ids in cases.values()), cases


def test_the_held_out_examples_are_the_ones_the_seed_draws() -> None:
    chance = random.Random(FIXTURE.get("seed"))  # noqa: S311 - a draw anyone can repeat, not a secret
    assert CONTRACTS
    for contract in CONTRACTS:
        drawn = [chance.choice(ids) for ids in change_cases(contract).values()]
        assert contract["held_out"] == drawn, contract["name"]


def test_each_patch_of_an_agent_is_recorded() -> None:
    names = {c["name"] for c in CONTRACTS}
    assert len(PATCHES) == 6
    kinds = sorted((p["contract"], p["kind"]) for p in PATCHES)
    assert kinds == sorted((n, k) for n in names for k in ("minimal", "special-cased"))
    for patch in PATCHES:
        assert (HERE / "patches" / f"{patch['contract']}.{patch['kind']}.diff").is_file()
        assert patch["visible"] in {"PASS", "FAIL", "ERROR", "ASK"}
        assert patch["all"] in {"PASS", "FAIL", "ERROR", "ASK"}


def audit(
    tmp: Path, contract: dict[str, Any], patch: Path, text: str, label: str
) -> dict[str, Any]:
    (project,) = [p for p in PROJECTS if p.name == contract["project"]]
    (case,) = [c for c in CASES if c.project == project.name and c.name == contract["name"]]
    checkout = tmp / "project"
    if not checkout.exists():
        clone(project, checkout)
    written = tmp / label / str(contract["name"]) / "contract.yaml"
    written.parent.mkdir(parents=True)
    written.write_text(text)
    out = tmp / f"out-{label}"
    temporary = tmp / f"temporary-{label}"
    temporary.mkdir()
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
            str(patch),
            "--contract",
            str(written),
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
    document: dict[str, Any] = json.loads(done.stdout)
    return document


SPECIAL = [p for p in PATCHES if p["kind"] == "special-cased"]


@pytest.mark.parametrize("patch", SPECIAL, ids=lambda p: p["contract"])
def test_a_special_cased_patch_passes_the_visible_and_fails_the_held_out(
    tmp_path: Path, patch: dict[str, Any]
) -> None:
    skip_unless_asked()
    require("git")
    require("podman")
    (contract,) = [c for c in CONTRACTS if c["name"] == patch["contract"]]
    diff = HERE / "patches" / f"{patch['contract']}.special-cased.diff"
    seen = audit(tmp_path, contract, diff, visible(contract), "visible")
    whole = audit(tmp_path, contract, diff, contract_path(contract).read_text(), "all")
    failing = [f for f in whole["findings"] if f["gate"] == "visible-examples"]
    caught = sorted({e for f in failing for e in re.findall(r"E-[0-9a-f]{4}", f["message"])})
    print(
        f"hold-out {contract['name']}: visible {seen['verdict']}, all {whole['verdict']}, {caught}"
    )
    assert seen["verdict"] == "PASS", seen
    assert whole["verdict"] == "FAIL", whole
    assert caught == sorted(contract["held_out"])
