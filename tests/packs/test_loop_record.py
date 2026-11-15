# SDD-EARS: PACKS-067 PACKS-070 PACKS-071 PACKS-072
from pathlib import Path

from dokime.core.outcomes import Outcome
from dokime.packs.selfcheck import turned_green
from tests.packs.doubles import BASE, FakeRepository, FakeRuntime
from tests.packs.loops import PROGRAMS, fixing_commit, not_a_witness, root, self_check

PASSED, FAILED, ERROR, SKIPPED = Outcome.PASSED, Outcome.FAILED, Outcome.ERROR, Outcome.SKIPPED


def test_a_short_history_is_decided_with_the_candidates_it_has(tmp_path: Path) -> None:
    repository = FakeRepository()
    one = fixing_commit(repository, root(repository), "one", 200)
    two = not_a_witness(repository, one, "two", 300)
    result = self_check(tmp_path, repository, FakeRuntime(), two)
    assert len(result.candidates) == 2
    ((finding),) = result.findings
    assert finding.code == "too-few-witnesses"
    assert "1 of 2" in finding.message


def test_each_candidate_records_its_commit_trees_images_bases_and_whether_it_is_a_witness(
    tmp_path: Path,
) -> None:
    repository = FakeRepository()
    one = fixing_commit(repository, root(repository), "one", 200)
    two = not_a_witness(repository, one, "two", 300)
    runtime = FakeRuntime()
    result = self_check(tmp_path, repository, runtime, two)
    assert [(c.commit, c.witness) for c in result.candidates] == [(two, False), (one, True)]
    images = [image for image, *_ in runtime.runs]
    sides = [side for c in result.candidates for side in (c.parent_side, c.commit_side)]
    assert [side.image for side in sides] == images
    assert {side.base for side in sides} == {BASE}
    assert all(side.tree in repository.trees for side in sides)
    assert sides[0].tree != sides[1].tree


def test_a_witness_records_the_tests_that_went_from_red_to_green(tmp_path: Path) -> None:
    repository = FakeRepository()
    one = fixing_commit(repository, root(repository), "one", 200)
    (candidate,) = self_check(tmp_path, repository, FakeRuntime(), one).candidates
    assert candidate.turned_green == ("tests/test_one.py", "tests/test_root.py")


def test_the_tests_that_turned_green_are_those_that_pass_now_and_did_not_before() -> None:
    parent = {"a": FAILED, "b": ERROR, "c": PASSED, "d": SKIPPED}
    commit = {"a": PASSED, "b": PASSED, "c": PASSED, "d": PASSED, "e": PASSED, "f": FAILED}
    assert turned_green(parent, commit) == ("a", "b", "e")


def test_the_result_records_once_the_programs_the_caller_names(tmp_path: Path) -> None:
    repository = FakeRepository()
    one = fixing_commit(repository, root(repository), "one", 200)
    assert self_check(tmp_path, repository, FakeRuntime(), one).programs == PROGRAMS
