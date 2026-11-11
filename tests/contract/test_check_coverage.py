# SDD-EARS: CONTRACT-070 CONTRACT-071
from dokime.contract.check import check
from dokime.core.verdicts import Verdict
from tests.contract.contracts import VALID, codes, line_of, only

E3 = VALID[VALID.index("  - id: E-0003") : VALID.index("\nrelations:")]


def test_a_requirement_without_an_example_asks_with_the_line_of_the_requirement() -> None:
    finding = only(check(VALID.replace(E3, "")), "requirement-without-example")
    assert finding.verdict is Verdict.ASK
    assert finding.lines == (line_of("  - id: keep-empty-invoices"),)
    assert "'keep-empty-invoices'" in finding.message


def test_a_requirement_with_only_model_examples_asks() -> None:
    finding = only(
        check(VALID.replace(E3, E3.replace("origin: human", "origin: model"))),
        "only-model-examples",
    )
    assert finding.verdict is Verdict.ASK
    assert finding.lines == (line_of("  - id: keep-empty-invoices"),)


def test_a_requirement_with_one_human_example_among_model_ones_does_not_ask() -> None:
    text = VALID.replace(
        "    origin: human\n    steps:\n      - input:\n          args: [[3",
        "    origin: model\n    steps:\n      - input:\n          args: [[3",
    )
    assert check(text).findings == ()


def test_an_example_with_a_defect_still_counts_for_its_requirement() -> None:
    checked = check(VALID.replace(E3, E3.replace("case: empty", "case: 3")))
    assert codes(checked) == ["wrong-type"]
