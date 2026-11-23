# SDD-EARS: CORPUS-084 CORPUS-085 CORPUS-086 CORPUS-087 CORPUS-088
import subprocess
import tomllib
from pathlib import Path
from typing import Any

import pytest

from tests.corpus.cases import BAD_LABELS, CASES, GATES, Case
from tests.corpus.sealing import (
    HELD_OUT,
    NOT_HERE,
    SEALED_GATE,
    judge,
    key_arguments,
    on_top,
    sealed_of,
)

RUN = Path(__file__).parent / "held-out-run.toml"
CONTRACT = "format: 1\nstory: a-story\nmay_modify_tests: []\nrequirements: []\nexamples: []\n"


def a_case(tmp_path: Path, label: str = HELD_OUT, sealed: bool = True) -> Case:
    good = tmp_path / "project" / "cases" / "a-story"
    good.mkdir(parents=True)
    (good / "contract.yaml").write_text(CONTRACT)
    if sealed:
        (good / "sealed.age").write_bytes(b"age-encryption.org/v1 sealed")
    bad = tmp_path / "project" / "cases" / "a-bad"
    bad.mkdir()
    fields = {
        "project": "project",
        "base": "HEAD",
        "contract": "../a-story/contract.yaml",
        "label": label,
        "expected": "FAIL",
        "failing_gate": SEALED_GATE,
    }
    (bad / "case.toml").write_text("".join(f'{k} = "{v}"\n' for k, v in fields.items()))
    return Case("project", "a-bad", bad)


def gate(name: str, verdict: str = "PASS", **more: str) -> dict[str, Any]:
    return {"gate": name, "status": "run", "verdict": verdict, **more}


NOT_APPLICABLE = {"gate": SEALED_GATE, "status": "not-applicable", "reason": NOT_HERE}


def test_the_label_and_the_gate_of_a_case_that_only_the_hold_out_catches() -> None:
    assert HELD_OUT in BAD_LABELS
    assert SEALED_GATE in GATES


def test_the_sealed_batch_of_a_case_is_the_one_next_to_its_contract(tmp_path: Path) -> None:
    case = a_case(tmp_path)
    assert sealed_of(case) == case.contract.parent / "sealed.age"
    assert sealed_of(a_case(tmp_path / "other", sealed=False)) is None


def git(directory: Path, *args: str) -> str:
    done = subprocess.run(
        ["git", "-C", str(directory), *args], capture_output=True, text=True, check=True
    )
    return done.stdout.strip()


def test_a_sealed_case_is_audited_on_a_commit_that_adds_its_contract_and_batch(
    tmp_path: Path,
) -> None:
    case = a_case(tmp_path)
    checkout = tmp_path / "checkout"
    checkout.mkdir()
    git(checkout, "init", "--quiet")
    (checkout / "code.py").write_text("x = 1\n")
    git(checkout, "add", ".")
    git(
        checkout,
        "-c",
        "user.name=t",
        "-c",
        "user.email=t@example.org",
        "commit",
        "--quiet",
        "-m",
        "base",
    )
    base = git(checkout, "rev-parse", "HEAD")
    top = on_top(checkout, case)
    assert git(checkout, "rev-parse", f"{top}^") == base
    files = git(checkout, "diff", "--name-only", base, top).splitlines()
    assert sorted(files) == [
        ".dokime/changes/a-story/contract.yaml",
        ".dokime/changes/a-story/sealed.age",
    ]


def test_without_the_key_a_held_out_case_passes_what_is_visible_and_is_not_applicable(
    tmp_path: Path,
) -> None:
    case = a_case(tmp_path)
    passing = {"verdict": "PASS", "gates": [gate("visible-examples"), NOT_APPLICABLE]}
    assert judge(case, passing, key=False) == []
    failing = {"verdict": "FAIL", "gates": [gate("visible-examples", "FAIL"), NOT_APPLICABLE]}
    assert judge(case, failing, key=False)
    ran = {"verdict": "PASS", "gates": [gate("visible-examples"), gate(SEALED_GATE)]}
    assert judge(case, ran, key=False)


def test_with_the_key_a_held_out_case_is_judged_on_its_expected(tmp_path: Path) -> None:
    case = a_case(tmp_path)
    caught = {"verdict": "FAIL", "gates": [gate("visible-examples"), gate(SEALED_GATE, "FAIL")]}
    assert judge(case, caught, key=True) == []
    missed = {"verdict": "PASS", "gates": [gate("visible-examples"), gate(SEALED_GATE)]}
    assert judge(case, missed, key=True)


@pytest.mark.parametrize(
    ("identity", "descriptor", "expected"),
    [
        (None, None, []),
        ("/keys/identity", 7, ["--identity", "/keys/identity", "--passphrase-fd", "7"]),
    ],
)
def test_the_identity_and_its_passphrase_go_to_audit_only_when_given(
    identity: str | None, descriptor: int | None, expected: list[str]
) -> None:
    assert key_arguments(identity, descriptor) == expected


def test_each_run_with_the_key_gives_the_expected_of_each_case_it_audited() -> None:
    recorded = tomllib.loads(RUN.read_text())
    by_key = {case.key: case for case in CASES}
    for run in recorded.get("run", []):
        assert run["date"]
        for audited in run["case"]:
            fields = by_key[audited["key"]].fields
            assert (audited["verdict"], audited["failing_gate"]) == (
                fields["expected"],
                fields.get("failing_gate", ""),
            )
