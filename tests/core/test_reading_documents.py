# SDD-EARS: CORE-020 CORE-021 CORE-022 CORE-023 CORE-024
import pytest

from dokime.core.reading import Reading, read
from dokime.core.verdicts import Verdict
from tests.core.reading_helpers import codes, lines_of


def test_a_clean_text_gives_its_value_and_no_finding() -> None:
    reading = read('story: rounding\nexamples:\n  - id: E-1\n    args: [1, "a", {k: true}]\n')
    assert reading.value == {
        "story": "rounding",
        "examples": [{"id": "E-1", "args": [1, "a", {"k": True}]}],
    }
    assert reading.findings == ()


def test_the_value_comes_together_with_every_finding() -> None:
    reading = read("a: 1\na: 2\nb: !!str 3\nc:\n  <<: {k: 1}\n")
    assert reading.value == {"a": 2, "b": 3, "c": {"<<": {"k": 1}}}
    assert sorted(codes(reading)) == ["duplicate-key", "merge-key", "tag"]


def test_every_finding_of_the_reader_fails() -> None:
    reading = read("a: 1\na: 2\nb: !!str 3\nc: &x 1\n")
    assert reading.findings
    assert {finding.verdict for finding in reading.findings} == {Verdict.FAIL}


@pytest.mark.parametrize(
    ("text", "line"),
    [
        ("a: [1, 2\nb: 3\n", 2),
        ("a: 1\nb: 'open\n", 3),
        ("a: 1\nb: \x00\n", 2),
        ("a: 1\n\tb: 2\n", 2),
    ],
)
def test_a_text_that_is_not_yaml_gives_no_value_and_one_finding_with_the_line(
    text: str, line: int
) -> None:
    reading = read(text)
    assert reading.value is None
    assert codes(reading) == ["not-yaml"]
    assert reading.findings[0].lines == (line,)


@pytest.mark.parametrize("text", ["", "# only a comment\n", "a: 1\n---\nb: 2\n"])
def test_a_text_without_exactly_one_document_gives_no_value_and_a_finding(text: str) -> None:
    reading = read(text)
    assert reading.value is None
    assert codes(reading) == ["not-one-document"]


def test_an_explicit_start_of_the_only_document_is_accepted() -> None:
    assert read("---\na: 1\n") == Reading(value={"a": 1}, findings=())


def test_each_anchor_and_alias_is_a_finding_with_its_line_and_there_is_no_value() -> None:
    reading = read("a: &first 1\nb: *first\nc: &second [1]\n")
    assert reading.value is None
    assert codes(reading) == ["anchor-or-alias"] * 3
    assert lines_of(reading, "anchor-or-alias") == [(1,), (2,), (3,)]
