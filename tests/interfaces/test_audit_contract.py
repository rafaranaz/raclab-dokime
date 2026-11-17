# SDD-EARS: INTERFACES-070 INTERFACES-071 INTERFACES-072 INTERFACES-073 INTERFACES-074
from pathlib import Path

import pytest

from dokime.core.verdicts import Verdict
from dokime.interfaces.inputs import read_contract
from tests.interfaces.audits import CONTRACT, CONTRACT_PATH, STORY, base, tree


def codes(findings: tuple[object, ...]) -> list[tuple[str, Verdict]]:
    return [(f.code, f.verdict) for f in findings]  # type: ignore[attr-defined]


def test_the_contract_of_the_story_is_read_from_the_tree_of_the_base(tmp_path: Path) -> None:
    read = read_contract(base(tmp_path), story=STORY)
    assert read.text == CONTRACT
    assert read.contract is not None
    assert read.contract.story == STORY


def test_a_contract_given_from_outside_is_read_from_its_file(tmp_path: Path) -> None:
    outside = tree(tmp_path / "case", {f"{STORY}/contract.yaml": CONTRACT}) / STORY
    read = read_contract(tree(tmp_path / "base", {}), outside=outside / "contract.yaml")
    assert read.text == CONTRACT
    assert read.contract is not None


@pytest.mark.parametrize("story", ["", "a/b", "../x", "1-story", "a b"])
def test_a_story_that_is_not_a_name_is_refused(tmp_path: Path, story: str) -> None:
    read = read_contract(base(tmp_path), story=story)
    assert codes(read.findings) == [("not-a-story", Verdict.ERROR)]
    assert read.contract is None


def test_the_findings_of_the_check_of_the_contract_are_given(tmp_path: Path) -> None:
    text = CONTRACT.replace(b"may_modify_tests: []", b"may_modify_tests: []\nunknown_field: 1")
    read = read_contract(base(tmp_path, **{CONTRACT_PATH.replace("/", "__"): text}), story=STORY)
    assert read.findings
    assert all(f.code != "story-not-directory" for f in read.findings)
    assert read.contract is None


def test_a_contract_from_outside_that_cannot_be_read_is_named(tmp_path: Path) -> None:
    read = read_contract(tree(tmp_path / "b", {}), outside=tmp_path / "absent" / "contract.yaml")
    assert codes(read.findings) == [("unreadable-file", Verdict.ERROR)]


def test_a_contract_is_read_for_a_story_or_from_a_file(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="neither"):
        read_contract(tree(tmp_path, {}))


def test_a_story_that_is_not_the_name_of_its_directory_is_refused(tmp_path: Path) -> None:
    outside = tree(tmp_path / "case", {"other-case/contract.yaml": CONTRACT})
    read = read_contract(tree(tmp_path / "b", {}), outside=outside / "other-case" / "contract.yaml")
    (found,) = read.findings
    assert (found.code, found.verdict) == ("story-not-directory", Verdict.ERROR)
    assert STORY in found.message
    assert "other-case" in found.message


def test_a_story_whose_directory_is_another_in_the_base_is_refused(tmp_path: Path) -> None:
    moved = {".dokime/changes/other-case/contract.yaml": CONTRACT}
    read = read_contract(tree(tmp_path, moved), story="other-case")
    assert codes(read.findings) == [("story-not-directory", Verdict.ERROR)]
