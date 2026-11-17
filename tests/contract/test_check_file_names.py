# SDD-EARS: CONTRACT-035
import pytest

from tests.contract.contracts import line_of, only, seeded

GIVEN = "            invoice.json: {$json: {lines: [3.335, 6.695]}}"
EXPECTED = "          exit: 0\n"


@pytest.mark.parametrize("name", ["../invoice.json", "/etc/invoice.json", "a/../../b", '""'])
def test_a_file_given_outside_the_working_directory_is_a_finding_that_names_it(name: str) -> None:
    finding = only(seeded(GIVEN, f"            {name}: hello"), "path-outside-directory")
    assert finding.lines == (line_of("          files:"),)
    assert name.strip('"') in finding.message


@pytest.mark.parametrize("name", ["../out.md", "/out.md"])
def test_a_file_expected_outside_the_working_directory_is_a_finding(name: str) -> None:
    expect = f"          exit: 0\n          files:\n            {name}: hello\n"
    only(seeded(EXPECTED, expect), "path-outside-directory")


@pytest.mark.parametrize("name", ["invoice.json", "data/invoice.json", "a..b.json"])
def test_a_file_inside_the_working_directory_is_accepted(name: str) -> None:
    assert seeded(GIVEN, f"            {name}: hello").findings == ()
