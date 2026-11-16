# SDD-EARS: CORPUS-020 CORPUS-021 CORPUS-022 CORPUS-023 CORPUS-024 CORPUS-025 CORPUS-026
import re

import pytest

from tests.corpus.cases import BAD_LABELS, CASES, GATES, GOOD, Case

EVERY = {"project", "base", "contract", "patch", "label", "how", "expected"}
BAD = EVERY | {"intent", "mechanism", "failing_gate"}


def test_the_corpus_holds_three_good_cases_and_seven_bad_ones() -> None:
    assert sorted(case.good for case in CASES) == [False] * 7 + [True] * 3


@pytest.mark.parametrize("case", CASES, ids=lambda case: case.key)
def test_a_case_holds_only_its_files(case: Case) -> None:
    names = sorted(path.name for path in case.directory.iterdir())
    expected = (
        ["case.toml", "contract.yaml", "patch.diff"] if case.good else ["case.toml", "patch.diff"]
    )
    assert names == expected


@pytest.mark.parametrize("case", CASES, ids=lambda case: case.key)
def test_a_case_holds_the_fields_of_its_kind_and_no_other(case: Case) -> None:
    fields = case.fields
    assert set(fields) == (EVERY if case.good else BAD)
    assert all(isinstance(value, str) and value and "\n" not in value for value in fields.values())
    assert fields["patch"] == "patch.diff"
    assert fields["label"] in (GOOD, *BAD_LABELS)
    if not case.good:
        assert fields["failing_gate"] in GATES


@pytest.mark.parametrize("case", CASES, ids=lambda case: case.key)
def test_the_project_of_a_case_is_the_directory_of_its_project(case: Case) -> None:
    assert case.fields["project"] == case.project


@pytest.mark.parametrize("case", CASES, ids=lambda case: case.key)
def test_the_base_of_a_case_is_the_full_name_of_a_commit(case: Case) -> None:
    assert re.fullmatch(r"[0-9a-f]{40}", str(case.fields["base"]))


@pytest.mark.parametrize("case", CASES, ids=lambda case: case.key)
def test_a_good_case_expects_pass_and_a_bad_one_fail(case: Case) -> None:
    assert case.fields["expected"] == ("PASS" if case.good else "FAIL")
