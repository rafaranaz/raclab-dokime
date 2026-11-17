# SDD-EARS: ORACLE-001 ORACLE-002 ORACLE-003 ORACLE-004 ORACLE-005 ORACLE-006 ORACLE-007 ORACLE-008
import pytest

from dokime.contract.expectations import Contains
from dokime.core.observation import Ending, Exited, Returned
from dokime.oracle.compare import Difference, compare
from tests.oracle.examples import example, observed


def test_each_step_is_compared_with_the_observation_in_its_position() -> None:
    two = example("function", {"returns": 1}, {"returns": 2})
    assert compare(two, observed(Returned(1), Returned(2))).holds
    swapped = compare(two, observed(Returned(2), Returned(1)))
    assert [d.step for d in swapped.differences] == [1, 2]


def test_an_example_whose_expectations_all_hold_gives_no_difference() -> None:
    comparison = compare(example("function", {"returns": [1, "a"]}), observed(Returned([1, "a"])))
    assert (comparison.example, comparison.holds, comparison.differences) == ("E-1", True, ())


def test_a_difference_names_the_step_the_part_the_expected_and_the_observed() -> None:
    comparison = compare(example("function", {"returns": 3}), observed(Returned(4)))
    assert comparison.differences == (Difference(step=1, part="returns", expected=3, observed=4),)


def test_only_the_parts_that_a_step_expects_are_compared() -> None:
    step = Exited(exit=1, stdout="anything", stderr="noise", files={"a": "x"})
    assert compare(example("cli", {"stdout": Contains("any")}), observed(step)).holds


def test_a_step_not_observed_because_of_the_limit_of_time_is_a_difference() -> None:
    comparison = compare(
        example("function", {"returns": 1}, {"returns": 2}),
        observed(Returned(1), ending=Ending.TIME_LIMIT),
    )
    (difference,) = comparison.differences
    assert (difference.step, difference.part, difference.observed) == (2, "step", "time-limit")


@pytest.mark.parametrize(
    ("ending", "said"),
    [
        ((9, None), "crashed by the signal 9"),
        ((None, 1), "crashed with the exit code 1"),
        ((None, None), "crashed"),
    ],
)
def test_a_step_not_observed_because_the_process_crashed_is_a_difference(
    ending: tuple[int | None, int | None], said: str
) -> None:
    signal, exit_code = ending
    comparison = compare(
        example("function", {"returns": 1}),
        observed(ending=Ending.CRASHED, signal=signal, exit_code=exit_code),
    )
    assert comparison.differences == (
        Difference(step=1, part="step", expected=None, observed=said),
    )


def test_the_observation_of_another_example_is_rejected_naming_both() -> None:
    with pytest.raises(ValueError, match=r"E-1.*E-2"):
        compare(example("function", {"returns": 1}), observed(Returned(1), name="E-2"))


def test_a_step_observed_at_another_boundary_is_a_difference() -> None:
    comparison = compare(example("function", {"returns": 0}), observed(Exited(0, "", "")))
    (difference,) = comparison.differences
    assert (difference.step, difference.part) == (1, "boundary")


def test_a_step_of_cli_observed_at_function_is_a_difference() -> None:
    comparison = compare(example("cli", {"exit": 0}), observed(Returned(0)))
    (difference,) = comparison.differences
    assert (difference.part, difference.expected, difference.observed) == (
        "boundary",
        "cli",
        "function",
    )
