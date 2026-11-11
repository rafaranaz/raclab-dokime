# SDD-EARS: CORE-040 CORE-041
from dokime.core.reading import read

TEXT = """\
story: rounding
requirements:
  - id: first
    kind: new
  - id: second
    kind: change
examples:
  - id: E-1
    steps:
      - input: {args: [1, 2]}
        expect:
          returns: 3
"""


def test_the_line_of_every_key_is_given_by_its_path() -> None:
    lines = read(TEXT).lines
    assert lines[("story",)] == 1
    assert lines[("requirements",)] == 2
    assert lines[("requirements", 1, "kind")] == 6
    assert lines[("examples", 0, "steps", 0, "expect", "returns")] == 12


def test_the_line_of_every_item_of_a_sequence_is_given_by_its_path() -> None:
    lines = read(TEXT).lines
    assert lines[("requirements", 0)] == 3
    assert lines[("requirements", 1)] == 5
    assert lines[("examples", 0, "steps", 0)] == 10
    assert lines[("examples", 0, "steps", 0, "input", "args", 1)] == 10


def test_the_root_is_the_empty_path() -> None:
    assert read("\n\nstory: rounding\n").lines[()] == 3


def test_every_part_of_the_value_has_a_line() -> None:
    reading = read(TEXT)

    def paths(value: object, prefix: tuple[str | int, ...] = ()) -> list[tuple[str | int, ...]]:
        found = [prefix]
        if isinstance(value, dict):
            for key, item in value.items():
                found += paths(item, (*prefix, key))
        if isinstance(value, list):
            for index, item in enumerate(value):
                found += paths(item, (*prefix, index))
        return found

    assert set(paths(reading.value)) == set(reading.lines)


def test_a_text_without_a_value_has_no_lines() -> None:
    assert read("a: &x 1\nb: *x\n").lines == {}


def test_a_repeated_key_has_the_line_of_the_occurrence_whose_value_is_kept() -> None:
    reading = read("id: a\nother: 1\nid: b\n")
    assert reading.value == {"id": "b", "other": 1}
    assert reading.lines[("id",)] == 3


def test_a_part_that_is_left_out_of_the_value_has_no_line() -> None:
    reading = read("a: 1\n? [x, y]\n: [no, 2]\n")
    assert reading.value == {"a": 1}
    assert set(reading.lines) == {(), ("a",)}
    assert [finding.code for finding in reading.findings] == ["key-not-text", "ambiguous-value"]
