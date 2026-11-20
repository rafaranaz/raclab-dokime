# SDD-EARS: CORPUS-066 CORPUS-067 CORPUS-068
"""The fixture of the sealed run of B1: the seal of each contract of B0, and what each patch expects
of its audit."""

import re
import tomllib
from collections import Counter
from pathlib import Path
from typing import Any

import pytest

from dokime.contract.check import check

HERE = Path(__file__).parent / "holdout-by-hand"
RUN: dict[str, Any] = tomllib.loads((HERE / "sealed-run.toml").read_text())
CONTRACTS: list[dict[str, Any]] = RUN["contract"]
PATCHES: list[dict[str, Any]] = RUN["patch"]
VERDICTS = {"PASS", "FAIL", "ERROR", "ASK"}


def whole(contract: dict[str, Any]) -> Any:
    read = check((HERE / contract["project"] / contract["name"] / "contract.yaml").read_text())
    assert read.contract is not None
    return read.contract


def sealed(contract: dict[str, Any]) -> Any:
    read = check((HERE / "sealed-run" / contract["name"] / "contract.yaml").read_text())
    assert read.contract is not None, read.findings
    return read.contract


def test_the_fixture_seals_the_three_contracts_of_b0() -> None:
    assert sorted(c["name"] for c in CONTRACTS) == [
        "format-a-blank-paragraph-between-blocks",
        "nextver-bumps-build-only-versions",
        "replace-keeps-the-constructor-error",
    ]


@pytest.mark.parametrize("contract", CONTRACTS, ids=lambda c: c["name"])
def test_each_seal_holds_out_one_example_of_each_case_of_two_or_more(
    contract: dict[str, Any],
) -> None:
    assert re.fullmatch(r"[0-9a-f]{40}", contract["batch_base"])
    assert isinstance(contract["seed"], int)
    assert 0 <= contract["seed"] < 2**53
    assert contract["kept_visible"] == []
    examples = whole(contract).examples
    sizes = Counter((e.requirement, e.case) for e in examples)
    held = [e for e in examples if e.id in contract["held_out"]]
    assert sorted(e.id for e in held) == sorted(contract["held_out"])
    assert sorted((e.requirement, e.case) for e in held) == sorted(
        case for case, size in sizes.items() if size >= 2
    )
    unheld = [(u["requirement"], u["case"], u["motive"]) for u in contract["without_holdout"]]
    assert unheld == [(r, c, "single-example") for (r, c), size in sizes.items() if size == 1]


@pytest.mark.parametrize("contract", CONTRACTS, ids=lambda c: c["name"])
def test_each_sealed_contract_is_the_visible_part_of_its_contract_of_b0(
    contract: dict[str, Any],
) -> None:
    visible = sealed(contract)
    ids = [e.id for e in whole(contract).examples]
    assert [e.id for e in visible.examples] == [i for i in ids if i not in contract["held_out"]]
    assert sorted(h.id for h in visible.held_out) == sorted(contract["held_out"])
    batch = (HERE / "sealed-run" / contract["name"] / "sealed.age").read_bytes()
    assert batch.startswith(b"age-encryption.org/v1\n")


def test_each_patch_of_b0_has_what_it_expects_with_its_reason() -> None:
    kinds = sorted((p["contract"], p["kind"]) for p in PATCHES)
    names = sorted(c["name"] for c in CONTRACTS)
    assert kinds == sorted((n, k) for n in names for k in ("minimal", "special-cased"))
    for patch in PATCHES:
        assert patch["expected"] in VERDICTS
        assert patch["expected_sealed"] in {"run PASS", "run FAIL", "not-reached"}
        assert ("expected_gate" in patch) == (patch["expected"] != "PASS")
        assert patch["why"]
        assert (HERE / "patches" / f"{patch['contract']}.{patch['kind']}.diff").is_file()
