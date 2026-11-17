# SDD-EARS: VERIFY-109 VERIFY-110
from dokime.verify.result import Checks
from tests.verify.runs import FAILED, PASSED, A, B, audit

C = "tests.test_c::test_three"


def test_the_checks_are_the_tests_that_passed_in_the_baseline() -> None:
    base = {A: PASSED, B: PASSED, C: FAILED}
    result, _ = audit((base, base), {A: PASSED, B: FAILED, C: PASSED})
    assert result.checks == (Checks("existing", 2),)


def test_an_unstable_test_is_not_a_check() -> None:
    result, _ = audit(({A: PASSED, B: PASSED}, {A: FAILED, B: PASSED}), {A: PASSED, B: PASSED})
    assert result.unstable == (A,)
    assert result.checks == (Checks("existing", 1),)


def test_no_test_passed_in_the_baseline_gives_no_checks() -> None:
    result, _ = audit(({A: FAILED},) * 2, {A: PASSED})
    assert result.checks == ()


def test_a_run_that_ends_with_a_finding_gives_no_checks() -> None:
    for result, _ in (audit("killed", {A: PASSED}), audit(({A: PASSED},), "killed")):
        assert result.findings[0].code == "run-killed"
        assert result.checks == ()
