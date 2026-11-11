# SDD-EARS: CORE-030 CORE-031 CORE-032 CORE-033 CORE-034 CORE-035 CORE-036
import math

import pytest

from dokime.core.reading import read
from tests.core.reading_helpers import codes, lines_of


def value_of(written: str) -> object:
    reading = read(f"first: 0\nv: {written}\n")
    assert reading.findings == (), written
    assert isinstance(reading.value, dict)
    return reading.value["v"]


def test_true_and_false_without_quotes_are_booleans() -> None:
    assert value_of("true") is True
    assert value_of("false") is False


def test_null_without_quotes_is_null() -> None:
    assert value_of("null") is None


@pytest.mark.parametrize(
    ("written", "number"),
    [("0", 0), ("7", 7), ("-3", -3), ("1048575", 1048575), ("999999999999", 999999999999)],
)
def test_an_integer_as_json_writes_it_is_an_integer(written: str, number: int) -> None:
    read_value = value_of(written)
    assert type(read_value) is int
    assert read_value == number


@pytest.mark.parametrize(
    ("written", "number"),
    [
        ("1.5", 1.5),
        ("-0.25", -0.25),
        ("3.335", 3.335),
        ("1.0", 1.0),
        ("10.0", 10.0),
        ("1e3", 1000.0),
        ("2.5E-3", 0.0025),
        ("1e+2", 100.0),
        ("0.005", 0.005),
    ],
)
def test_a_number_with_decimals_or_exponent_as_json_writes_it_is_a_float(
    written: str, number: float
) -> None:
    read_value = value_of(written)
    assert type(read_value) is float
    assert math.isclose(read_value, number)


AMBIGUOUS = {
    "words": ["yes", "No", "ON", "off", "y", "N", "True", "FALSE", "Null", "NULL", "~"],
    "leading zeros": ["010", "-007", "00", "01.5"],
    "other bases": ["0x10", "0o10", "0b10", "0XFF"],
    "underscores": ["1_000", "1_000.5", "-1_0"],
    "plus or bare dot": ["+1", "+1.5", ".5", "-.5", "1.", "+.5"],
    "infinities": [".inf", "-.inf", "+.Inf", ".nan", ".NaN"],
    "dates and times": [
        "2026-11-10",
        "2026-11-10T10:00:00Z",
        "2026-11-10 10:00:00",
        "12:30",
        "1:30:00",
    ],
}


@pytest.mark.parametrize("written", [form for forms in AMBIGUOUS.values() for form in forms])
def test_a_form_of_the_table_of_ambiguous_values_is_a_finding_with_its_line(written: str) -> None:
    reading = read(f"first: 0\nv: {written}\n")
    assert codes(reading) == ["ambiguous-value"]
    assert lines_of(reading, "ambiguous-value") == [(2,)]
    assert repr(written) in reading.findings[0].message


def test_an_empty_value_is_a_finding_with_its_line() -> None:
    reading = read("first: 0\nv:\nlast:\n  -\n  - 2\n")
    assert lines_of(reading, "ambiguous-value") == [(2,), (4,)]


@pytest.mark.parametrize("written", ["1.10", "2.50", "1.00", "-3.140", "1.10e3"])
def test_a_number_with_two_or_more_decimals_ending_in_zero_is_a_finding(written: str) -> None:
    reading = read(f"first: 0\nv: {written}\n")
    assert codes(reading) == ["ambiguous-value"]
    assert lines_of(reading, "ambiguous-value") == [(2,)]


@pytest.mark.parametrize(
    "written",
    [
        "github",
        "EUR",
        "invoice.json",
        "1.0 MB",
        "E-4f1a",
        "tools.clean:clean",
        "v1.10",
        "a_b",
        "2026-11-10 release notes",
        "a-b",
        "x-1",
        "1-2",
        "trueish",
        "nullable",
        "yesterday",
        "1,5",
    ],
)
def test_a_value_without_quotes_in_no_other_form_is_a_text(written: str) -> None:
    assert value_of(written) == written


@pytest.mark.parametrize(
    "written",
    ["no", "true", "null", "1.10", "010", "2026-11-10", "", "~", "1_000", "42", "1.5"],
)
def test_a_value_in_quotes_is_always_a_text(written: str) -> None:
    assert value_of(f'"{written}"') == written
    assert value_of(f"'{written}'") == written


def test_a_rejected_value_stays_in_the_value_as_it_was_written() -> None:
    reading = read("v: no\nw: 1.10\n")
    assert reading.value == {"v": "no", "w": "1.10"}
