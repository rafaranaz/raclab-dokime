# SDD-EARS: CORE-150 CORE-151 CORE-152 CORE-153
import re
from pathlib import PurePosixPath

import pytest

from dokime.core.layout import POLICY, change_directory, contract_path


def test_the_policy_is_in_the_directory_of_the_harness() -> None:
    assert PurePosixPath(".dokime/policy.yaml") == POLICY


def test_the_directory_of_a_change_is_named_by_its_story() -> None:
    assert change_directory("invoice-rounding") == PurePosixPath(".dokime/changes/invoice-rounding")


def test_the_contract_of_a_change_is_in_its_directory() -> None:
    assert contract_path("invoice-rounding") == PurePosixPath(
        ".dokime/changes/invoice-rounding/contract.yaml"
    )


@pytest.mark.parametrize(
    "story", ["", "..", "a/b", "1st", "-a", "a-", "a--b", "a b", "a_b", "/etc", "a.b"]
)
def test_a_story_that_is_not_a_name_is_refused_naming_it(story: str) -> None:
    with pytest.raises(ValueError, match=re.escape(f"{story!r} is not a name")):
        change_directory(story)
    with pytest.raises(ValueError, match="is not a name"):
        contract_path(story)


@pytest.mark.parametrize("story", ["a", "A1", "invoice-rounding", "x-2-y"])
def test_a_story_that_is_a_name_is_accepted(story: str) -> None:
    assert change_directory(story).name == story
