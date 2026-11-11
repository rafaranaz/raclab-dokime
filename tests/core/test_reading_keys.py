# SDD-EARS: CORE-025 CORE-026 CORE-027 CORE-028 CORE-029
import pytest

from dokime.core.reading import Reading, read
from tests.core.reading_helpers import codes, lines_of


@pytest.mark.parametrize(
    "text", ["a: 1\nb: !!str 2\n", "a: 1\nb: !custom 2\n", "a: 1\nb: !!map {}\n"]
)
def test_an_explicit_tag_is_a_finding_with_the_line_of_the_node(text: str) -> None:
    reading = read(text)
    assert codes(reading) == ["tag"]
    assert lines_of(reading, "tag") == [(2,)]


def test_a_merge_key_without_quotes_is_a_finding_with_its_line() -> None:
    reading = read("base: {k: 1}\nother:\n  <<: {k: 2}\n")
    assert codes(reading) == ["merge-key"]
    assert lines_of(reading, "merge-key") == [(3,)]


def test_a_quoted_key_that_looks_like_a_merge_key_is_a_text() -> None:
    assert read('a:\n  "<<": 1\n') == Reading(value={"a": {"<<": 1}}, findings=())


@pytest.mark.parametrize("text", ["a: 1\n? [x, y]\n: 2\n", "a: 1\n? {x: 1}\n: 2\n"])
def test_a_key_that_is_a_sequence_or_a_mapping_is_a_finding_with_its_line(text: str) -> None:
    reading = read(text)
    assert codes(reading) == ["key-not-text"]
    assert lines_of(reading, "key-not-text") == [(2,)]
    assert reading.value == {"a": 1}


def test_every_key_is_read_as_a_text_as_it_is_written() -> None:
    reading = read("1: a\ntrue: b\nno: c\n1.10: d\n'quoted': e\n")
    assert reading.value == {"1": "a", "true": "b", "no": "c", "1.10": "d", "quoted": "e"}
    assert reading.findings == ()


def test_a_repeated_key_is_one_finding_that_names_it_and_lists_every_line() -> None:
    reading = read("id: a\nother: 1\nid: b\nnested:\n  id: c\nid: d\n")
    assert codes(reading) == ["duplicate-key"]
    assert lines_of(reading, "duplicate-key") == [(1, 3, 6)]
    assert "'id'" in reading.findings[0].message


def test_each_repeated_key_has_its_own_finding() -> None:
    reading = read("a: 1\na: 2\nb:\n  c: 1\n  c: 2\n  c: 3\n")
    assert lines_of(reading, "duplicate-key") == [(1, 2), (4, 5, 6)]


def test_a_key_written_in_two_forms_is_the_same_key() -> None:
    reading = read("1: a\n'1': b\n")
    assert lines_of(reading, "duplicate-key") == [(1, 2)]
