# SDD-EARS: CONTRACT-016 CONTRACT-017
from dokime.contract.check import check
from tests.contract.contracts import VALID, codes, line_of, only, seeded


def test_a_repeated_requirement_id_is_one_finding_with_every_line() -> None:
    finding = only(check(VALID.replace("keep-empty-invoices", "round-total-once")), "duplicate-id")
    assert finding.lines == (
        line_of("  - id: round-total-once"),
        line_of("  - id: keep-empty-invoices"),
    )
    assert "'round-total-once'" in finding.message


def test_a_repeated_example_id_is_one_finding_with_every_line() -> None:
    text = VALID.replace("  - id: E-0002", "  - id: E-0001").replace(
        "  - id: E-0003", "  - id: E-0001"
    )
    finding = only(check(text), "duplicate-id")
    assert finding.lines == (
        line_of("  - id: E-0001"),
        line_of("  - id: E-0002"),
        line_of("  - id: E-0003"),
    )


def test_a_repeated_relation_id_is_a_finding() -> None:
    second = (
        "  - id: L1\n    requirement: round-total-once\n    relation: idempotent\n    target: x\n"
    )
    finding = only(check(VALID + second), "duplicate-id")
    assert finding.lines == (line_of("  - id: L1"), VALID.count("\n") + 1)


def test_the_same_id_in_two_sections_is_not_repeated() -> None:
    assert check(VALID.replace("  - id: L1", "  - id: E-0001")).findings == ()


def test_a_literal_block_outside_text_is_a_finding_with_its_line() -> None:
    old = (
        "          stdout:\n            $text: |\n"
        "              total: 10.03\n            final_newline: true\n"
    )
    checked = seeded(old, "          stdout: |\n            total: 10.03\n")
    assert only(checked, "block-outside-text").lines == (line_of(old),)


def test_a_literal_block_in_a_requirement_text_is_a_finding() -> None:
    old = "    text: While an invoice has no lines, the system shall return a total of zero.\n"
    new = (
        "    text: |\n"
        "      While an invoice has no lines, the system shall return a total of zero.\n"
    )
    assert "block-outside-text" in codes(seeded(old, new))
