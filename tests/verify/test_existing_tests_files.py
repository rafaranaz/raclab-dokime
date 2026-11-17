# SDD-EARS: VERIFY-105 VERIFY-106 VERIFY-107
import pytest

from dokime.core.verdicts import Verdict
from tests.verify.runs import PASSED, A, B, audit, found


def test_a_test_that_passed_in_the_baseline_and_disappears_fails() -> None:
    result, _ = audit(({A: PASSED, B: PASSED},) * 2, {B: PASSED})
    assert found(result) == [("existing-test-disappears", Verdict.FAIL)]
    assert A in result.findings[0].message


@pytest.mark.parametrize(
    ("test", "file"),
    [
        (A, "tests/test_a.py"),
        (B, "tests/test_a.py"),
        ("docs.usage.rst::usage.rst", "docs/usage.rst"),
    ],
)
def test_a_test_of_an_authorised_file_that_disappears_asks(test: str, file: str) -> None:
    result, _ = audit(({test: PASSED},) * 2, {}, authorised=(file,))
    assert found(result) == [("authorised-test-disappears", Verdict.ASK)]


@pytest.mark.parametrize(
    "test", ["tests.test_ab::test_one", "tests::test_a", "other.tests.test_a::t"]
)
def test_a_test_of_another_file_is_not_of_the_authorised_one(test: str) -> None:
    result, _ = audit(({test: PASSED},) * 2, {}, authorised=("tests/test_a.py",))
    assert found(result) == [("existing-test-disappears", Verdict.FAIL)]
