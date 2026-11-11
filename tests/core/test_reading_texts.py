# SDD-EARS: CORE-037 CORE-038 CORE-039
import pytest

from dokime.core.reading import Reading, read
from tests.core.reading_helpers import codes, lines_of


def test_a_literal_block_that_ends_in_one_newline_is_read_as_it_is() -> None:
    reading = read("first: 0\ntext: |\n  one\n\n  two\nlast: 1\n")
    assert reading == Reading(value={"first": 0, "text": "one\n\ntwo\n", "last": 1}, findings=())


@pytest.mark.parametrize(
    "text",
    [
        "first: 0\ntext: >\n  one\n  two\n",
        "first: 0\ntext: >-\n  one\n",
        "first: 0\ntext: one\n  two\n",
        'first: 0\ntext: "one\n  two"\n',
        "first: 0\ntext: 'one\n\n  two'\n",
        "first: 0\ntext: [a, one\n  two]\n",
    ],
)
def test_a_scalar_on_several_lines_that_is_not_a_literal_block_is_a_finding(text: str) -> None:
    reading = read(text)
    assert codes(reading) == ["text-on-several-lines"]
    assert lines_of(reading, "text-on-several-lines") == [(2,)]


def test_a_key_on_several_lines_is_a_finding_too() -> None:
    reading = read("first: 0\n? one\n  two\n: 1\n")
    assert lines_of(reading, "text-on-several-lines") == [(2,)]


@pytest.mark.parametrize(
    "text",
    ['first: 0\ntext: "one line"\nother: plain words here\n', "first: 0\nlist: [a, b,\n  c]\n"],
)
def test_a_scalar_on_one_line_is_not_a_finding(text: str) -> None:
    assert read(text).findings == ()


@pytest.mark.parametrize(
    "text",
    [
        "first: 0\ntext: |-\n  one\n",
        "first: 0\ntext: |+\n  one\n\nlast: 1\n",
        "first: 0\ntext: |\nlast: 1\n",
    ],
)
def test_a_literal_block_that_does_not_end_in_exactly_one_newline_is_a_finding(text: str) -> None:
    reading = read(text)
    assert codes(reading) == ["block-ending"]
    assert lines_of(reading, "block-ending") == [(2,)]


def test_a_keep_block_with_no_blank_line_after_it_reads_as_a_literal_block() -> None:
    assert read("text: |+\n  one\n") == Reading(value={"text": "one\n"}, findings=())


def test_a_line_of_a_literal_block_that_ends_in_a_space_or_a_tab_is_a_finding() -> None:
    reading = read("first: 0\ntext: |\n  one\n  two  \n  three\n  four\t\n")
    assert codes(reading) == ["trailing-whitespace"] * 2
    assert lines_of(reading, "trailing-whitespace") == [(4,), (6,)]


def test_the_findings_of_a_text_come_in_the_order_of_their_lines() -> None:
    reading = read("a: |-\n  x\nb: no\nc: >\n  y\nb: 1\n")
    assert [(finding.code, finding.lines) for finding in reading.findings] == [
        ("block-ending", (1,)),
        ("ambiguous-value", (3,)),
        ("duplicate-key", (3, 6)),
        ("text-on-several-lines", (4,)),
    ]
