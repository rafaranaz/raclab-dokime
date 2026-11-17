# SDD-EARS: ORACLE-030 ORACLE-031 ORACLE-032
from dokime.contract.expectations import Contains, Expected, FullMatch
from dokime.core.observation import Exited
from dokime.oracle.compare import Difference, compare
from tests.oracle.examples import example, observed

RAN = Exited(exit=2, stdout="1.2.4\n", stderr="error: no\n", files={"out.md": "# Title\n"})


def test_the_exit_the_output_and_the_error_hold_by_the_rules_of_the_contract() -> None:
    expect: dict[str, Expected] = {
        "exit": 2,
        "stdout": "1.2.4\n",
        "stderr": FullMatch(r"error: .*\n"),
    }
    assert compare(example("cli", expect), observed(RAN)).holds
    (difference,) = compare(example("cli", {"exit": 0}), observed(RAN)).differences
    assert difference == Difference(step=1, part="exit", expected=0, observed=2)


def test_each_file_expected_holds_for_the_file_of_that_name() -> None:
    assert compare(example("cli", {"files": {"out.md": Contains("Title")}}), observed(RAN)).holds
    assert not compare(example("cli", {"files": {"out.md": "other"}}), observed(RAN)).holds


def test_a_file_expected_that_was_not_written_is_a_difference_that_names_it() -> None:
    (difference,) = compare(example("cli", {"files": {"gone.md": "x"}}), observed(RAN)).differences
    assert (difference.part, difference.observed) == ("files/gone.md", "not written")
