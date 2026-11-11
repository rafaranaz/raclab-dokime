# SDD-EARS: CONTRACT-010 CONTRACT-011 CONTRACT-012 CONTRACT-013 CONTRACT-014 CONTRACT-015
import pytest

from dokime.contract.check import check
from tests.contract.contracts import VALID, codes, line_of, only, seeded


@pytest.mark.parametrize("text", ["- a\n- b\n", "just a text\n", "7\n"])
def test_a_contract_that_is_not_a_mapping_is_one_finding_and_nothing_else(text: str) -> None:
    finding = only(check(text), "wrong-type")
    assert finding.lines == (1,)


@pytest.mark.parametrize(
    ("old", "new", "field"),
    [
        ("story: invoice-rounding", "story: invoice-rounding\nowner: rafa", "owner"),
        ("    kind: preserve", "    kind: preserve\n    priority: high", "priority"),
        ("    case: empty", "    case: empty\n    tags: [a]", "tags"),
        ("      - input: {args: [[]]}", "      - input: {args: [[]]}\n        note: x", "note"),
        ("{args: [[]]}", "{args: [[]], timeout: 3}", "timeout"),
        (
            "expect: {returns: {total: 0, currency: EUR}}",
            "expect: {returns: 0, prints: x}",
            "prints",
        ),
        ("          exit: 0", "          exit: 0\n          signal: 9", "signal"),
        (
            "          args: [invoice.json]",
            "          args: [invoice.json]\n          cwd: /tmp",
            "cwd",
        ),
        ("    over: lines", "    over: lines\n    seed: 3", "seed"),
    ],
)
def test_a_field_that_the_table_does_not_list_is_a_finding_with_its_line(
    old: str, new: str, field: str
) -> None:
    finding = only(seeded(old, new), "unknown-field")
    assert repr(field) in finding.message
    assert finding.lines == (line_of(old) + new.count("\n") if "\n" in new else line_of(old),)


@pytest.mark.parametrize(
    ("piece", "field", "at"),
    [
        ("format: 1\n", "format", "format: 1"),
        ("story: invoice-rounding\n", "story", "format: 1"),
        ("    kind: preserve\n", "kind", "  - id: keep-empty-invoices"),
        ("    source: written\n  - id: keep", "source", "  - id: round-total-once"),
        ("    case: empty\n", "case", "  - id: E-0003"),
        ("    origin: human\n    steps:\n      - input: {args", "origin", "  - id: E-0003"),
        ("    target: billing.totals:invoice_total\n    over", "target", "  - id: L1"),
        ("    over: lines\n", "over", "  - id: L1"),
    ],
)
def test_a_missing_mandatory_field_is_a_finding_with_the_line_of_its_mapping(
    piece: str, field: str, at: str
) -> None:
    kept = "" if piece.endswith("\n") else piece.split("\n", 1)[1]
    finding = only(seeded(piece, kept), "missing-field")
    assert repr(field) in finding.message
    assert finding.lines == (line_of(at),)


@pytest.mark.parametrize(
    ("old", "new"),
    [
        ("story: invoice-rounding", "story: Invoice rounding!"),
        ("may_modify_tests: [tests/test_totals.py]", "may_modify_tests: tests/test_totals.py"),
        ("may_modify_tests: [tests/test_totals.py]", "may_modify_tests: [1, 2]"),
        ("  - id: keep-empty-invoices", "  - id: keep empty invoices"),
        ("    case: empty", "    case: 3"),
        ("target: invoice total", "target: [invoice, total]"),
        (
            "    target: billing.totals:invoice_total\n"
            "    origin: human\n    steps:\n      - input: {",
            "    target: invoice_total\n    origin: human\n    steps:\n      - input: {",
        ),
        ("description: Two lines in euros whose sum needs rounding.", 'description: "two\\nlines"'),
        ("      - input: {args: [[]]}", "      - input: [[]]"),
        ("{args: [[]]}", "{args: nothing}"),
        ("kwargs: {currency: EUR}", "kwargs: [EUR]"),
        ("          args: [invoice.json]", "          args: [1, 2]"),
        ("          exit: 0", '          exit: "0"'),
        ("          exit: 0", "          exit: true"),
        ("    over: lines", "    over: [lines]"),
    ],
)
def test_a_value_that_is_not_what_the_table_states_is_a_finding_with_its_line(
    old: str, new: str
) -> None:
    finding = only(seeded(old, new), "wrong-type")
    assert finding.lines == (line_of(old),)


def test_a_list_item_that_is_not_a_mapping_is_a_finding() -> None:
    finding = only(seeded("relations:\n", "relations:\n  - just a text\n"), "wrong-type")
    assert finding.lines == (line_of("relations:\n") + 1,)


@pytest.mark.parametrize(
    ("old", "new", "allowed"),
    [
        ("format: 1", "format: 2", "1"),
        ("format: 1", 'format: "1"', "1"),
        ("kind: preserve", "kind: keep", "new, change, preserve"),
        (
            "    source: written\n  - id: keep",
            "    source: copied\n  - id: keep",
            "written, imported",
        ),
        ("boundary: cli", "boundary: grpc", "function, cli, http"),
        (
            "    origin: human\n    steps:\n      - input: {",
            "    origin: person\n    steps:\n      - input: {",
            "human, model",
        ),
        ("relation: order-insensitive", "relation: commutative", "idempotent, order-insensitive"),
    ],
)
def test_a_value_outside_a_closed_list_is_a_finding_that_lists_the_values(
    old: str, new: str, allowed: str
) -> None:
    finding = only(seeded(old, new), "unknown-value")
    assert allowed in finding.message
    assert finding.lines == (line_of(old),)


def test_a_contract_without_requirements_is_a_finding() -> None:
    text = VALID[: VALID.index("requirements:")] + "requirements: []\nexamples: []\n"
    finding = only(check(text), "empty-list")
    assert finding.lines == (5,)


def test_an_example_without_steps_is_a_finding() -> None:
    old = (
        "    steps:\n      - input: {args: [[]]}\n"
        "        expect: {returns: {total: 0, currency: EUR}}\n"
    )
    checked = seeded(old, "    steps: []\n")
    assert "empty-list" in codes(checked)
    assert only(checked, "empty-list").lines == (line_of(old),)


def test_a_contract_may_have_no_examples() -> None:
    text = VALID[: VALID.index("examples:")] + "examples: []\n"
    assert set(codes(check(text))) == {"requirement-without-example"}


def test_a_cli_step_may_give_standard_input_and_environment() -> None:
    old = "          args: [invoice.json]"
    new = old + '\n          stdin: "3.335\\n6.695\\n"\n          env: {LANG: C}'
    assert seeded(old, new).findings == ()


@pytest.mark.parametrize("section", ["requirements", "examples", "relations"])
def test_a_section_that_is_not_a_list_is_one_finding(section: str) -> None:
    start = VALID.index(f"{section}:")
    end = VALID.find("\n\n", start)
    text = VALID[:start] + f"{section}: none" + (VALID[end:] if end != -1 else "\n")
    assert "wrong-type" in codes(check(text))
    assert codes(check(text)).count("wrong-type") == 1


def test_an_example_or_a_step_that_is_not_a_mapping_is_a_finding() -> None:
    checked = seeded("relations:\n", "  - not an example\nrelations:\n")
    assert only(checked, "wrong-type").lines == (line_of("relations:\n"),)
    old = "      - input: {args: [[]]}\n        expect: {returns: {total: 0, currency: EUR}}\n"
    assert only(seeded(old, "      - not a step\n"), "wrong-type").lines == (line_of(old),)


def test_an_item_without_its_id_is_one_finding() -> None:
    finding = only(seeded("  - id: L1\n    requirement", "  - requirement"), "missing-field")
    assert "'id'" in finding.message


def test_a_relation_with_a_defect_is_not_returned() -> None:
    checked = seeded("    over: lines", "    over: lines\n    seed: 3")
    assert checked.contract is None


def test_a_requirement_that_is_not_a_mapping_is_one_finding() -> None:
    checked = seeded("\nexamples:", "  - not a requirement\n\nexamples:")
    assert only(checked, "wrong-type").lines == (line_of("\nexamples:"),)
