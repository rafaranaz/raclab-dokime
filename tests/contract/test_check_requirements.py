# SDD-EARS: CONTRACT-020 CONTRACT-021 CONTRACT-022
import pytest

from dokime.contract.check import check
from tests.contract.contracts import VALID, line_of, only, seeded

TEXT = "    text: While an invoice has no lines, the system shall return a total of zero.\n"


def with_text(text: str) -> str:
    return VALID.replace(TEXT, f"    text: {text}\n")


@pytest.mark.parametrize(
    "text",
    [
        "The system shall round the total once.",
        "tabulate shall write a pipe character in a cell without a backslash.",
        "When a cell contains a pipe character, tabulate shall write it after a backslash.",
        "While no cell contains a pipe character, tabulate shall return the same table.",
        "While the format is github, when a cell is empty, tabulate shall write a space.",
        "If the invoice has no currency, then the system shall reject it with an error.",
        "Where rounding is configured, the system shall round each line first.",
        "The cleaner shall leave unchanged every line that is not a link, a separator or blank.",
    ],
)
def test_a_text_in_one_of_the_five_templates_is_accepted(text: str) -> None:
    assert check(with_text(text)).findings == ()


@pytest.mark.parametrize(
    "text",
    [
        "Round the total once.",
        "The system rounds the total once.",
        "When an invoice has lines the system shall round the total.",
        "If the invoice has no currency, the system shall reject it.",
        "The system shall round the total once",
        "When an invoice arrives, shall round the total.",
        "The system should round the total once.",
    ],
)
def test_a_text_in_no_template_is_a_finding_that_names_the_requirement(text: str) -> None:
    finding = only(check(with_text(text)), "not-ears")
    assert "'keep-empty-invoices'" in finding.message
    assert finding.lines == (line_of(TEXT),)


def test_a_text_with_shall_twice_is_a_finding_that_names_the_requirement() -> None:
    text = "When an invoice arrives, the system shall round it and the log shall record it."
    finding = only(check(with_text(text)), "not-ears")
    assert "'keep-empty-invoices'" in finding.message
    assert finding.lines == (line_of(TEXT),)


def test_replaces_on_a_change_is_accepted() -> None:
    checked = seeded("    kind: preserve", "    kind: change\n    replaces: round-per-line")
    assert checked.findings == ()
    assert checked.contract is not None
    assert checked.contract.requirements[1].replaces == "round-per-line"


@pytest.mark.parametrize("kind", ["new", "preserve"])
def test_replaces_on_another_kind_is_a_finding_with_the_line_of_the_field(kind: str) -> None:
    checked = seeded("    kind: preserve", f"    kind: {kind}\n    replaces: round-per-line")
    assert only(checked, "replaces-without-change").lines == (line_of("    kind: preserve") + 1,)
