# SDD-EARS: CONTRACT-001 CONTRACT-002 CONTRACT-003 CONTRACT-004 CONTRACT-005 CONTRACT-006
from dokime.contract.check import check
from dokime.contract.notes import Notes
from dokime.core.reading import read
from dokime.core.verdicts import Verdict
from tests.contract.contracts import VALID, codes, line_of, seeded


def test_a_valid_contract_has_no_finding_and_is_returned() -> None:
    checked = check(VALID)
    assert checked.findings == ()
    assert checked.verdict is Verdict.PASS
    assert checked.contract is not None
    assert checked.contract.story == "invoice-rounding"
    assert checked.contract.may_modify_tests == ("tests/test_totals.py",)
    assert [r.id for r in checked.contract.requirements] == [
        "round-total-once",
        "keep-empty-invoices",
    ]
    assert [e.id for e in checked.contract.examples] == ["E-0001", "E-0002", "E-0003"]
    assert [r.relation for r in checked.contract.relations] == ["order-insensitive"]


def test_the_optional_lists_may_be_left_out() -> None:
    text = VALID[: VALID.index("relations:")].replace(
        "may_modify_tests: [tests/test_totals.py]\n", ""
    )
    checked = check(text)
    assert checked.findings == ()
    assert checked.contract is not None
    assert checked.contract.may_modify_tests == ()
    assert checked.contract.relations == ()


def test_the_findings_of_the_reader_are_reported_with_those_of_the_contract() -> None:
    checked = seeded("case: empty", "case: empty\n    case: other\n    colour: red")
    assert codes(checked) == ["duplicate-key", "unknown-field"]


def test_a_text_the_reader_gives_no_value_for_has_only_the_findings_of_the_reader() -> None:
    checked = check("format: 1\nstory: &name x\nrequirements: *name\n")
    assert codes(checked) == ["anchor-or-alias", "anchor-or-alias"]
    assert checked.contract is None


def test_every_finding_is_reported_at_once_in_the_order_of_the_lines() -> None:
    text = VALID.replace("kind: preserve", "kind: keep").replace("origin: human", "origin: me", 1)
    text = text.replace("story: invoice-rounding", "story: 7")
    checked = check(text)
    assert [(f.code, f.lines) for f in checked.findings] == [
        ("wrong-type", (2,)),
        ("unknown-value", (line_of("kind: preserve"),)),
        (
            "unknown-value",
            (line_of("    origin: human\n    steps:\n      - input:\n          args: [[3"),),
        ),
    ]


def test_a_finding_fails_unless_its_requirement_names_another_verdict() -> None:
    checked = seeded("kind: preserve", "kind: keep")
    assert [f.verdict for f in checked.findings] == [Verdict.FAIL]
    assert checked.verdict is Verdict.FAIL


def test_a_contract_with_a_failing_finding_is_not_returned() -> None:
    assert seeded("kind: preserve", "kind: keep").contract is None


def test_a_contract_with_an_error_finding_is_not_returned() -> None:
    checked = seeded("boundary: cli", "boundary: http")
    assert checked.verdict is Verdict.ERROR
    assert checked.contract is None


def test_a_contract_that_only_asks_is_returned() -> None:
    text = VALID.replace(
        "\nexamples:",
        "  - id: no-examples-yet\n    kind: new\n"
        "    text: The system shall log every total.\n    source: written\n\nexamples:",
    )
    checked = check(text)
    assert checked.verdict is Verdict.ASK
    assert checked.contract is not None
    assert len(checked.contract.requirements) == 3


def test_a_part_without_a_line_of_its_own_takes_the_line_of_what_contains_it() -> None:
    notes = Notes(read("a:\n  b: 1\n"))
    assert notes.line(("a", "b")) == 2
    assert notes.line(("a", "missing", "deeper")) == 1
    assert notes.line(("nowhere",)) == 1
