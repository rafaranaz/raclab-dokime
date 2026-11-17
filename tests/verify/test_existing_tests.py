# SDD-EARS: VERIFY-044 VERIFY-100 VERIFY-101 VERIFY-102 VERIFY-103 VERIFY-104 VERIFY-108
import pytest

from dokime.core.verdicts import Verdict
from tests.verify.doubles import Files, patch
from tests.verify.runs import FAILED, PASSED, SKIPPED, A, B, audit, found, outcomes


@pytest.mark.parametrize("runs", [1, 2, 3])
def test_the_base_runs_as_many_times_as_the_policy_says_and_the_change_once(runs: int) -> None:
    _, runtime = audit(({A: PASSED},), {A: PASSED}, runs=runs)
    sources = [run["src/p.py"] for run in runtime.runs]
    assert sources == ["code"] * runs + ["new"]


def test_the_change_runs_the_tests_of_the_base_unless_authorised() -> None:
    files: Files = {"tests/test_a.py": b"base", "tests/test_b.py": b"base", "conftest.py": b"base"}
    changed = patch(
        {
            "outcomes.json": outcomes({A: PASSED}),
            "tests/test_a.py": "patched",
            "tests/test_b.py": "authorised",
            "tests/conftest.py": "added",
            "conftest.py": "patched",
        }
    )
    _, runtime = audit(
        ({A: PASSED},), {}, files=files, changed=changed, authorised=("tests/test_b.py",)
    )
    change = runtime.runs[-1]
    assert {path: change[path] for path in change if path != "outcomes.json"} == {
        "conftest.py": "base",
        "src/p.py": "code",
        "tests/test_a.py": "base",
        "tests/test_b.py": "authorised",
    }


def test_tests_that_still_pass_pass() -> None:
    result, _ = audit(({A: PASSED, B: PASSED},) * 2, {A: PASSED, B: PASSED, "new::t": FAILED})
    assert (result.findings, result.unstable) == ((), ())


@pytest.mark.parametrize("outcome", [FAILED, "error", SKIPPED])
def test_a_test_that_passed_in_the_baseline_and_no_longer_passes_fails(outcome: str) -> None:
    result, _ = audit(({A: PASSED, B: PASSED},) * 2, {A: outcome, B: PASSED})
    assert found(result) == [("existing-test-fails", Verdict.FAIL)]
    assert A in result.findings[0].message
    assert outcome in result.findings[0].message


def test_a_test_that_did_not_pass_on_the_base_is_not_compared() -> None:
    result, _ = audit(({A: FAILED, B: SKIPPED},) * 2, {})
    assert result.findings == ()


def test_a_test_whose_outcome_varies_in_the_baseline_is_left_out_and_listed() -> None:
    base = ({A: PASSED, B: PASSED, "c::t": PASSED}, {A: FAILED, B: PASSED})
    result, _ = audit(base, {A: FAILED})
    assert result.unstable == ("c::t", A)
    assert found(result) == [("existing-test-disappears", Verdict.FAIL)]
    assert B in result.findings[0].message


def test_only_a_test_that_passed_in_every_run_of_the_base_counts() -> None:
    base = ({A: PASSED}, {A: PASSED}, {A: SKIPPED})
    result, _ = audit(base, {}, runs=3)
    assert (result.findings, result.unstable) == ((), (A,))


def test_a_run_of_the_base_that_ends_with_a_finding_is_an_error() -> None:
    result, runtime = audit("killed", {A: PASSED})
    assert found(result) == [("run-killed", Verdict.ERROR)]
    assert len(runtime.runs) == 1


def test_a_run_of_the_change_that_ends_with_a_finding_is_an_error() -> None:
    result, _ = audit(({A: PASSED},), "killed")
    assert found(result) == [("run-killed", Verdict.ERROR)]


def test_a_patch_that_does_not_apply_is_an_error() -> None:
    result, _ = audit(({A: PASSED},), {}, changed=patch(removes=["src/missing.py"]))
    assert found(result) == [("patch-does-not-apply", Verdict.ERROR)]
