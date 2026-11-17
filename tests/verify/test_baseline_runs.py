# SDD-EARS: VERIFY-060 VERIFY-063 VERIFY-064
import pytest

from dokime.core.verdicts import Verdict
from tests.verify.gates import codes, contract, example, on_base, run_baseline


@pytest.mark.parametrize("runs", [1, 2, 3])
def test_the_examples_are_observed_on_the_base_as_many_times_as_the_policy_says(runs: int) -> None:
    _, observer = on_base(contract(example("E-1", "R-keep")), {"E-1": 2}, runs=runs)
    assert len(observer.calls) == runs


@pytest.mark.parametrize("requirement", ["R-keep", "R-new"])
def test_an_example_that_varies_between_the_runs_of_the_base_asks_and_is_listed(
    requirement: str,
) -> None:
    given = contract(example("E-1", requirement), example("E-2", "R-keep"))
    result, _ = run_baseline(given, [{"E-1": 2, "E-2": 2}, {"E-1": 3, "E-2": 2}], runs=2)
    assert codes(list(result.findings)) == [("example-varies-on-base", Verdict.ASK)]
    assert "E-1" in result.findings[0].message
    assert result.unstable == ("E-1",)


def test_an_example_that_fails_the_same_in_every_run_does_not_vary() -> None:
    result, _ = run_baseline(contract(example("E-1", "R-keep")), [{"E-1": 3}, {"E-1": 4}], runs=2)
    assert codes(list(result.findings)) == [("preserved-example-fails-on-base", Verdict.FAIL)]
    assert result.unstable == ()
