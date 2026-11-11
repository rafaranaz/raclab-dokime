# SDD-EARS: CONTRACT-040 CONTRACT-041 CONTRACT-042 CONTRACT-043 CONTRACT-044 CONTRACT-045
import pytest

from dokime.contract.expectations import AnyValue, FullMatch
from tests.contract.contracts import line_of, only, seeded

RETURNS = "          returns: {total: {$approx: 10.03, tolerance: 0.005}, currency: EUR}"
E3_EXPECT = "        expect: {returns: {total: 0, currency: EUR}}"
E3_INPUT = "      - input: {args: [[]]}"


def returning(expectation: str) -> str:
    return f"        expect: {{returns: {expectation}}}"


def test_a_directive_outside_the_table_is_a_finding_that_names_it() -> None:
    finding = only(seeded(E3_EXPECT, returning("{$startswith: tot}")), "unknown-directive")
    assert "$startswith" in finding.message
    assert finding.lines == (line_of(E3_EXPECT),)


def test_a_mapping_with_two_directives_is_a_finding() -> None:
    checked = seeded(E3_EXPECT, returning("{$contains: a, $fullmatch: b}"))
    assert only(checked, "several-directives").lines == (line_of(E3_EXPECT),)


@pytest.mark.parametrize(
    ("expectation", "parameter"),
    [
        ("{$contains: total, case: lower}", "case"),
        ("{$approx: 1.5, tolerance: 0.1, relative: true}", "relative"),
        ("{$any: uuid, version: 4}", "version"),
    ],
)
def test_a_parameter_the_directive_does_not_have_is_a_finding(
    expectation: str, parameter: str
) -> None:
    finding = only(seeded(E3_EXPECT, returning(expectation)), "directive-parameter")
    assert repr(parameter) in finding.message
    assert finding.lines == (line_of(E3_EXPECT),)


def test_approx_without_its_tolerance_is_a_finding() -> None:
    finding = only(
        seeded(RETURNS, "          returns: {total: {$approx: 10.03}}"), "directive-parameter"
    )
    assert "'tolerance'" in finding.message
    assert finding.lines == (line_of(RETURNS),)


def test_text_without_final_newline_is_a_finding() -> None:
    finding = only(seeded("            final_newline: true\n", ""), "directive-parameter")
    assert "'final_newline'" in finding.message


@pytest.mark.parametrize(
    "expectation",
    [
        "{$contains: 5}",
        "{$fullmatch: [a]}",
        '{$fullmatch: "(unclosed"}',
        '{$approx: "ten", tolerance: 0.1}',
        "{$approx: true, tolerance: 0.1}",
        "{$approx: 10.03, tolerance: -0.1}",
        '{$approx: 10.03, tolerance: "small"}',
        "{$unordered: a}",
        "{$any: number}",
        '{$text: "not a block", final_newline: true}',
    ],
)
def test_a_directive_value_that_is_not_what_the_table_states_is_a_finding(
    expectation: str,
) -> None:
    checked = seeded(E3_EXPECT, returning(expectation))
    assert only(checked, "directive-value").lines == (line_of(E3_EXPECT),)


def test_final_newline_that_is_not_true_or_false_is_a_finding() -> None:
    checked = seeded("            final_newline: true", '            final_newline: "yes"')
    assert only(checked, "directive-value").lines == (line_of("            final_newline: true"),)


@pytest.mark.parametrize(
    "value",
    ["{$contains: a}", "{$approx: 1.5, tolerance: 0.1}", "{$any: uuid}", "{$unordered: [1]}"],
)
def test_a_matcher_in_an_input_is_a_finding_with_its_line(value: str) -> None:
    checked = seeded(E3_INPUT, f"      - input: {{args: [{value}]}}")
    assert only(checked, "matcher-in-input").lines == (line_of(E3_INPUT),)


def test_a_key_that_starts_with_a_dollar_inside_a_matcher_is_checked_too() -> None:
    checked = seeded(E3_EXPECT, returning("{$unordered: [{$nope: 1}]}"))
    only(checked, "unknown-directive")


def test_the_matchers_of_the_table_are_accepted_and_returned() -> None:
    expectation = "{id: {$any: uuid}, at: {$any: timestamp}, code: {$fullmatch: 'E-[0-9]+'}}"
    checked = seeded(E3_EXPECT, returning(expectation))
    assert checked.findings == ()
    assert checked.contract is not None
    assert checked.contract.examples[2].steps[0].expect["returns"] == {
        "id": AnyValue("uuid"),
        "at": AnyValue("timestamp"),
        "code": FullMatch("E-[0-9]+"),
    }
