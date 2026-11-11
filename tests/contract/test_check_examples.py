# SDD-EARS: CONTRACT-030 CONTRACT-031 CONTRACT-032 CONTRACT-033
from dokime.core.verdicts import Verdict
from tests.contract.contracts import line_of, only, seeded

E1_REQUIREMENT = "    requirement: round-total-once\n    case: normal\n    boundary: function"
E3_EXPECT = "        expect: {returns: {total: 0, currency: EUR}}"


def test_an_example_that_names_an_unknown_requirement_is_a_finding_with_its_line() -> None:
    new = E1_REQUIREMENT.replace("round-total-once", "round-twice")
    finding = only(seeded(E1_REQUIREMENT, new), "unknown-requirement")
    assert finding.lines == (line_of(E1_REQUIREMENT),)
    assert "'round-twice'" in finding.message


def test_a_relation_that_names_an_unknown_requirement_is_a_finding_with_its_line() -> None:
    old = "    requirement: round-total-once\n    relation:"
    checked = seeded(old, "    requirement: round-twice\n    relation:")
    assert only(checked, "unknown-requirement").lines == (line_of(old),)


def test_an_example_at_the_http_boundary_is_an_error_finding_with_its_line() -> None:
    finding = only(seeded("boundary: cli", "boundary: http"), "not-supported-yet")
    assert finding.verdict is Verdict.ERROR
    assert finding.lines == (line_of("boundary: cli"),)


def test_a_function_step_may_expect_an_exception() -> None:
    new = "        expect: {raises: {type: ValueError, message: {$contains: no lines}}}"
    assert seeded(E3_EXPECT, new).findings == ()


def test_a_function_step_that_expects_returns_and_raises_is_a_finding() -> None:
    new = "        expect: {returns: 0, raises: {type: ValueError}}"
    assert only(seeded(E3_EXPECT, new), "two-expectations").lines == (line_of(E3_EXPECT),)


def test_a_function_step_that_expects_nothing_is_a_finding() -> None:
    assert only(seeded(E3_EXPECT, "        expect: {}"), "no-expectation").lines == (
        line_of(E3_EXPECT),
    )


def test_a_cli_step_that_expects_nothing_is_a_finding() -> None:
    old = (
        "        expect:\n          exit: 0\n          stdout:\n            $text: |\n"
        "              total: 10.03\n            final_newline: true\n"
    )
    assert only(seeded(old, "        expect: {}\n"), "no-expectation").lines == (line_of(old),)
