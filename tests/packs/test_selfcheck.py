# SDD-EARS: PACKS-020 PACKS-021 PACKS-030 PACKS-031 PACKS-032 PACKS-033 PACKS-034 PACKS-035
import pytest

from dokime.packs.check import check
from dokime.packs.model import Pack
from dokime.packs.selfcheck import Outcome, is_candidate, is_witness, self_check
from tests.packs.packs import VALID

PASSED, FAILED, ERROR, SKIPPED = Outcome.PASSED, Outcome.FAILED, Outcome.ERROR, Outcome.SKIPPED


def pack() -> Pack:
    checked = check(VALID)
    assert checked.pack is not None
    return checked.pack


@pytest.mark.parametrize(
    "path",
    [
        "tests/test_cache.py",
        "tests/unit/deep/test_x.py",
        "tests/data/sample.json",
        "src/cachetools/test_keys.py",
        "src/a/b/test_c.py",
    ],
)
def test_a_path_that_matches_a_pattern_is_a_test(path: str) -> None:
    assert pack().is_test(path)


@pytest.mark.parametrize(
    "path",
    [
        "src/cachetools/keys.py",
        "README.md",
        "testsuite/test_x.py",
        "docs/tests/x.py",
        "src/cachetools/sub/keys_test.py",
        "test_root.py",
    ],
)
def test_a_path_that_matches_no_pattern_is_not_a_test(path: str) -> None:
    assert not pack().is_test(path)


def test_a_commit_that_changes_a_test_and_other_code_is_a_candidate() -> None:
    assert is_candidate(pack(), ["src/cachetools/keys.py", "tests/test_keys.py", "CHANGELOG.rst"])


@pytest.mark.parametrize(
    "changed",
    [["tests/test_keys.py", "tests/test_cache.py"], ["src/cachetools/keys.py", "README.md"], []],
)
def test_a_commit_that_changes_only_tests_or_only_other_code_is_not_a_candidate(
    changed: list[str],
) -> None:
    assert not is_candidate(pack(), changed)


@pytest.mark.parametrize("before", [FAILED, ERROR])
def test_a_test_that_passes_on_the_commit_and_not_on_the_parent_makes_a_witness(
    before: Outcome,
) -> None:
    parent = {"test_old": PASSED, "test_new": before}
    commit = {"test_old": PASSED, "test_new": PASSED}
    assert is_witness(parent, commit)


def test_a_test_missing_from_a_parent_report_with_an_error_makes_a_witness() -> None:
    parent = {"test_old": PASSED, "tests/test_keys.py": ERROR}
    commit = {"test_old": PASSED, "test_new": PASSED}
    assert is_witness(parent, commit)


@pytest.mark.parametrize(
    "parent",
    [
        {},
        {"test_old": PASSED},
        {"test_old": PASSED, "test_new": PASSED},
        {"test_old": PASSED, "test_new": SKIPPED},
    ],
)
def test_a_parent_report_without_a_failure_or_an_error_makes_no_witness(
    parent: dict[str, Outcome],
) -> None:
    assert not is_witness(parent, {"test_old": PASSED, "test_new": PASSED})


@pytest.mark.parametrize(
    "commit",
    [{}, {"test_new": FAILED}, {"test_new": ERROR}, {"test_new": SKIPPED}, {"test_other": PASSED}],
)
def test_a_test_that_fails_on_the_parent_and_does_not_pass_on_the_commit_makes_no_witness(
    commit: dict[str, Outcome],
) -> None:
    assert not is_witness({"test_new": FAILED, "test_other": PASSED}, commit)


@pytest.mark.parametrize(
    "candidates",
    [[True, True], [False, True, False, True], [False] * 8 + [True, True], [True] * 12],
)
def test_two_witnesses_among_the_first_ten_candidates_give_no_finding(
    candidates: list[bool],
) -> None:
    assert self_check(candidates) == ()
