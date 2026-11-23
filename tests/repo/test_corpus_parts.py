# SDD-EARS: REPO-161 REPO-162 REPO-163
import subprocess
import sys

import pytest

from tools.corpus_parts import PARTS, part_of

AUDIT = "tests/corpus/test_corpus_audit.py::test_a_case_gets_its_expected_verdict_at_its_gate"


@pytest.mark.parametrize(
    ("nodeid", "part"),
    [
        (f"{AUDIT}[mdformat/format-a-blank-paragraph-between-blocks]", "a"),
        (f"{AUDIT}[mdformat/fixes-only-a-code-block-before-the-blank]", "e"),
        (f"{AUDIT}[python-semver/replace-keeps-the-constructor-error]", "b"),
        (f"{AUDIT}[python-semver/nextver-fixes-only-patch]", "f"),
        (f"{AUDIT}[cachetools/a-case]", "b"),
        (f"{AUDIT}[cachetools/another-case]", "f"),
        (f"{AUDIT}[another-project/a-case]", "d"),
        (
            "tests/corpus/test_corpus_holdout_by_hand.py::test_the_fixture_has_the_three_contracts",
            "c",
        ),
        ("tests/corpus/test_corpus_sealed_run.py::test_a_sealed_contract", "c"),
        ("tests/corpus/test_corpus_sealed_run_fixture.py::test_the_fixture_seals", "d"),
        ("tests/corpus/test_corpus_self_check.py::test_the_pack[mdformat]", "d"),
        ("tests/corpus/test_corpus_witnesses.py::test_x", "d"),
    ],
)
def test_each_test_of_the_corpus_has_its_part(nodeid: str, part: str) -> None:
    assert part_of(nodeid) == part


def collect(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-p",
            "no:cacheprovider",
            "--collect-only",
            "-q",
            *arguments,
        ],
        capture_output=True,
        text=True,
        check=False,
    )


def ids(result: subprocess.CompletedProcess[str]) -> list[str]:
    return [line for line in result.stdout.splitlines() if "::" in line]


def test_the_parts_hold_each_test_of_the_corpus_once() -> None:
    whole = ids(collect("tests/corpus"))
    parts = {
        p: ids(collect("-p", "tools.corpus_parts", "--corpus-part", p, "tests/corpus"))
        for p in PARTS
    }
    assert all(parts.values())
    assert sorted(t for found in parts.values() for t in found) == sorted(whole)
    assert all(part_of(t) == p for p, found in parts.items() for t in found)


def test_a_part_that_is_not_one_stops_the_run() -> None:
    result = collect("-p", "tools.corpus_parts", "--corpus-part", "g", "tests/corpus")
    assert result.returncode != 0
    assert "'g'" in result.stdout + result.stderr
    assert not ids(result)


def test_there_are_six_parts() -> None:
    assert PARTS == ("a", "b", "c", "d", "e", "f")
