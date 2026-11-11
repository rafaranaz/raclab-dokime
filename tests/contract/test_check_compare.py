# SDD-EARS: CONTRACT-080 CONTRACT-081 CONTRACT-082 CONTRACT-083 CONTRACT-084 CONTRACT-085
from dokime.contract.check import check
from tests.contract.contracts import VALID, codes, line_of, only

E3 = VALID[VALID.index("  - id: E-0003") : VALID.index("\nrelations:")]
E3_LINE = line_of("  - id: E-0003")
E4_LINE = E3_LINE + E3.count("\n")


def with_a_fourth(expect: str, *, case: str = "empty", inputs: str = "{args: [[]]}") -> str:
    """The valid contract plus an example like the third, with another id and expectation."""
    fourth = (
        E3.replace("E-0003", "E-0004")
        .replace("case: empty", f"case: {case}")
        .replace("{args: [[]]}", inputs)
        .replace("{returns: {total: 0, currency: EUR}}", expect)
    )
    return VALID.replace(E3, E3 + fourth)


def test_two_examples_with_the_same_steps_are_a_duplicate_that_names_both() -> None:
    finding = only(
        check(with_a_fourth("{returns: {total: 0, currency: EUR}}", case="again")),
        "duplicate-example",
    )
    assert finding.lines == (E3_LINE, E4_LINE)
    assert "'E-0003'" in finding.message
    assert "'E-0004'" in finding.message


def test_two_different_exact_values_for_the_same_input_contradict() -> None:
    finding = only(
        check(with_a_fourth("{returns: {total: 1, currency: EUR}}")), "contradictory-examples"
    )
    assert finding.lines == (E3_LINE, E4_LINE)
    assert "'E-0003'" in finding.message
    assert "'E-0004'" in finding.message


def test_the_same_number_with_another_type_contradicts() -> None:
    only(check(with_a_fourth("{returns: {total: 0.0, currency: EUR}}")), "contradictory-examples")


def test_an_exact_value_that_does_not_satisfy_a_matcher_contradicts() -> None:
    expect = "{returns: {total: {$approx: 5, tolerance: 0.5}, currency: EUR}}"
    assert only(check(with_a_fourth(expect)), "contradictory-examples").lines == (E3_LINE, E4_LINE)


def test_an_exact_value_that_satisfies_a_matcher_does_not_contradict() -> None:
    expect = "{returns: {total: {$approx: 0.2, tolerance: 0.5}, currency: EUR}}"
    assert check(with_a_fourth(expect)).findings == ()


def test_returns_and_raises_for_the_same_input_contradict() -> None:
    finding = only(check(with_a_fourth("{raises: {type: ValueError}}")), "contradictory-examples")
    assert finding.lines == (E3_LINE, E4_LINE)


def test_two_matchers_for_the_same_field_are_not_compared() -> None:
    third = "{returns: {total: {$approx: 0, tolerance: 0.1}, currency: EUR}}"
    text = with_a_fourth("{returns: {total: {$approx: 9, tolerance: 0.1}, currency: EUR}}")
    text = text.replace(
        "        expect: {returns: {total: 0, currency: EUR}}", f"        expect: {third}", 1
    )
    assert check(text).findings == ()


def test_examples_with_other_inputs_targets_or_boundaries_are_not_compared() -> None:
    assert (
        check(
            with_a_fourth("{returns: {total: 1, currency: EUR}}", inputs="{args: [[0]]}")
        ).findings
        == ()
    )
    other_target = with_a_fourth("{returns: {total: 1, currency: EUR}}").replace(
        "    target: billing.totals:invoice_total\n"
        "    origin: human\n    steps:\n      - input: {args: [[]]}\n"
        "        expect: {returns: {total: 1",
        "    target: billing.totals:other\n"
        "    origin: human\n    steps:\n      - input: {args: [[]]}\n"
        "        expect: {returns: {total: 1",
    )
    assert check(other_target).findings == ()


def test_later_steps_are_compared_while_the_inputs_are_the_same() -> None:
    steps = "      - input: {args: [[]]}\n        expect: {returns: {total: 0, currency: EUR}}\n"
    second_a = "      - input: {args: [[1]]}\n        expect: {returns: 1}\n"
    second_b = "      - input: {args: [[1]]}\n        expect: {returns: 2}\n"
    fourth = E3.replace("E-0003", "E-0004").replace(steps, steps + second_b)
    text = VALID.replace(E3, E3.replace(steps, steps + second_a) + fourth)
    finding = only(check(text), "contradictory-examples")
    assert finding.lines == (E3_LINE, E4_LINE + 2)


def test_cli_expectations_are_compared_field_by_field_and_file_by_file() -> None:
    e2 = VALID[VALID.index("  - id: E-0002") : VALID.index("  - id: E-0003")]
    stdout = (
        "          stdout:\n            $text: |\n"
        "              total: 10.03\n            final_newline: true\n"
    )
    same_input_other_fields = e2.replace("E-0002", "E-0005").replace(
        "          exit: 0\n" + stdout, '          stderr: ""\n          files: {out.txt: done}\n'
    )
    assert check(VALID.replace(e2, e2 + same_input_other_fields)).findings == ()
    other_exit = e2.replace("E-0002", "E-0005").replace(
        "          exit: 0\n" + stdout, "          exit: 2\n"
    )
    only(check(VALID.replace(e2, e2 + other_exit)), "contradictory-examples")


def test_an_example_with_a_defect_is_left_out_of_the_comparison() -> None:
    text = with_a_fourth("{returns: {total: 1, currency: EUR}}", case="3")
    assert codes(check(text)) == ["wrong-type"]
    text = with_a_fourth("{returns: {total: {$nope: 1}, currency: EUR}}")
    assert codes(check(text)) == ["unknown-directive"]


def test_a_matcher_first_and_an_exact_value_second_are_compared_too() -> None:
    third = "{returns: {total: {$approx: 5, tolerance: 0.5}, currency: EUR}}"
    text = with_a_fourth("{returns: {total: 0, currency: EUR}}", case="again")
    text = text.replace(
        "        expect: {returns: {total: 0, currency: EUR}}", f"        expect: {third}", 1
    )
    only(check(text), "contradictory-examples")


def test_two_examples_with_the_same_matchers_are_a_duplicate() -> None:
    expect = "{returns: {$json: {items: {$unordered: [1, {$contains: a}]}}}}"
    text = with_a_fourth(expect).replace(
        "        expect: {returns: {total: 0, currency: EUR}}", f"        expect: {expect}", 1
    )
    only(check(text), "duplicate-example")
    other = with_a_fourth("{returns: {$json: {items: {$unordered: [2, {$contains: a}]}}}}").replace(
        "        expect: {returns: {total: 0, currency: EUR}}", f"        expect: {expect}", 1
    )
    assert check(other).findings == ()
