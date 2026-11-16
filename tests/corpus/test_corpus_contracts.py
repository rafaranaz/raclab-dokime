# SDD-EARS: CORPUS-027 CORPUS-028 CORPUS-029 CORPUS-033
import tomllib

import pytest

from dokime.contract.check import check
from dokime.core.verdicts import Verdict
from tests.corpus.cases import CASES, Case
from tests.corpus.projects import HERE

GOOD = [case for case in CASES if case.good]
BAD = [case for case in CASES if not case.good]


@pytest.mark.parametrize("case", GOOD, ids=lambda case: case.key)
def test_a_good_case_uses_its_own_contract(case: Case) -> None:
    assert case.fields["contract"] == "contract.yaml"


@pytest.mark.parametrize("case", BAD, ids=lambda case: case.key)
def test_a_bad_case_uses_the_contract_of_a_good_case_of_its_project_and_its_base(
    case: Case,
) -> None:
    (good,) = [other for other in GOOD if other.directory / "contract.yaml" == case.contract]
    assert (good.project, good.fields["base"]) == (case.project, case.fields["base"])


@pytest.mark.parametrize("case", GOOD, ids=lambda case: case.key)
def test_the_contract_of_a_good_case_passes_the_check_of_contracts(case: Case) -> None:
    checked = check(case.contract.read_text(encoding="utf-8"))
    assert (checked.verdict, checked.findings) == (Verdict.PASS, ())


@pytest.mark.parametrize("case", GOOD, ids=lambda case: case.key)
def test_the_story_of_a_good_contract_is_the_name_of_its_case(case: Case) -> None:
    checked = check(case.contract.read_text(encoding="utf-8"))
    assert checked.contract is not None
    assert checked.contract.story == case.name


def test_the_review_confirms_every_case_with_its_date_and_minutes() -> None:
    with (HERE / "review.toml").open("rb") as handle:
        review = tomllib.load(handle)
    assert sorted(review["confirmed"]) == sorted(case.key for case in CASES)
    assert isinstance(review["date"], str)
    assert isinstance(review["minutes"], int)
    assert review["by"] == "the maintainer"
