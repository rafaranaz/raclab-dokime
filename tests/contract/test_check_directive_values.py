# SDD-EARS: CONTRACT-046 CONTRACT-047 CONTRACT-048 CONTRACT-049 CONTRACT-050
import json

from dokime.contract.check import check
from dokime.contract.expectations import Approx, Json
from dokime.contract.model import Example
from dokime.core.verdicts import Verdict
from tests.contract.contracts import VALID, line_of, only, seeded

E3_EXPECT = "        expect: {returns: {total: 0, currency: EUR}}"
E3_INPUT = "      - input: {args: [[]]}"


def example(text: str, index: int) -> Example:
    checked = check(text)
    assert checked.findings == (), [(f.code, f.lines, f.message) for f in checked.findings]
    assert checked.contract is not None
    return checked.contract.examples[index]


def test_the_matcher_ref_is_an_error_finding_with_its_line() -> None:
    new = '        expect: {returns: {$ref: "steps[0].returns"}}'
    finding = only(seeded(E3_EXPECT, new), "not-supported-yet")
    assert finding.verdict is Verdict.ERROR
    assert finding.lines == (line_of(E3_EXPECT),)


def test_a_text_with_final_newline_true_keeps_the_text_of_the_block() -> None:
    assert example(VALID, 1).steps[0].expect["stdout"] == "total: 10.03\n"


def test_a_text_with_final_newline_false_loses_the_newline_that_ends_the_block() -> None:
    text = VALID.replace("            final_newline: true", "            final_newline: false")
    assert example(text, 1).steps[0].expect["stdout"] == "total: 10.03"


def test_a_text_of_several_lines_keeps_its_inner_newlines() -> None:
    text = VALID.replace(
        "              total: 10.03\n            final_newline: true",
        "              total: 10.03\n\n              lines: 2\n            final_newline: false",
    )
    assert example(text, 1).steps[0].expect["stdout"] == "total: 10.03\n\nlines: 2"


def test_a_text_may_be_an_input() -> None:
    new = (
        "      - input:\n          args:\n            - $text: |\n"
        "                one\n              final_newline: false"
    )
    assert example(VALID.replace(E3_INPUT, new), 2).steps[0].input["args"] == ["one"]


def test_a_literal_value_is_given_as_written_without_reading_what_is_inside() -> None:
    new = '        expect: {returns: {$literal: {$contains: a, "$ref": 1, plain: [true]}}}'
    step = example(VALID.replace(E3_EXPECT, new), 2).steps[0]
    assert step.expect["returns"] == {"$contains": "a", "$ref": 1, "plain": [True]}


def test_a_literal_value_may_be_an_input() -> None:
    new = "      - input: {args: [{$literal: {$approx: 1}}]}"
    assert example(VALID.replace(E3_INPUT, new), 2).steps[0].input["args"] == [{"$approx": 1}]


def test_a_json_in_an_input_is_the_text_of_its_value_written_as_json() -> None:
    content = example(VALID, 1).steps[0].input["files"]
    assert isinstance(content, dict)
    assert isinstance(content["invoice.json"], str)
    assert json.loads(content["invoice.json"]) == {"lines": [3.335, 6.695]}


def test_a_json_in_an_expectation_is_a_matcher_on_the_value_inside() -> None:
    new = "        expect: {returns: {$json: {total: {$approx: 0, tolerance: 0.5}}}}"
    step = example(VALID.replace(E3_EXPECT, new), 2).steps[0]
    assert step.expect["returns"] == Json({"total": Approx(0.0, 0.5)})
