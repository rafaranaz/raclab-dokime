# SDD-EARS: CORE-050 CORE-051 CORE-052 CORE-053 CORE-054
from dokime.core.reading import read
from dokime.core.shape import Field, Notes, check_fields, one_of
from dokime.core.verdicts import Verdict

TABLE = {
    "name": Field("a text", lambda value: isinstance(value, str)),
    "level": one_of("P1", "P2", "P3"),
    "format": one_of(1),
    "note": Field("a text", lambda value: isinstance(value, str), mandatory=False),
}
TEXT = "name: cachetools\nlevel: P1\nformat: 1\n"


def checked(text: str) -> Notes:
    reading = read(text)
    assert isinstance(reading.value, dict)
    notes = Notes(reading)
    check_fields(notes, reading.value, (), TABLE)
    return notes


def found(text: str) -> list[tuple[str, tuple[int, ...]]]:
    return [(finding.code, finding.lines) for finding in checked(text).findings]


def test_a_mapping_that_fits_its_table_has_no_finding() -> None:
    assert found(TEXT) == []
    assert found(TEXT + "note: by hand\n") == []


def test_a_field_the_table_does_not_list_is_a_finding_that_names_it_with_its_line() -> None:
    notes = checked(TEXT + "colour: red\n")
    assert found(TEXT + "colour: red\n") == [("unknown-field", (4,))]
    assert "'colour'" in notes.findings[0].message
    assert notes.findings[0].verdict is Verdict.FAIL


def test_a_missing_mandatory_field_is_a_finding_with_the_line_of_the_mapping() -> None:
    notes = checked("\nname: cachetools\nformat: 1\n")
    assert [(f.code, f.lines) for f in notes.findings] == [("missing-field", (2,))]
    assert "'level'" in notes.findings[0].message


def test_a_value_that_is_not_what_the_table_states_is_a_finding_with_its_line() -> None:
    notes = checked("name: [a]\nlevel: P1\nformat: 1\n")
    assert [(f.code, f.lines) for f in notes.findings] == [("wrong-type", (1,))]
    assert "'name' holds a text" in notes.findings[0].message


def test_a_value_outside_a_closed_list_is_a_finding_that_lists_the_values() -> None:
    notes = checked("name: x\nlevel: P9\nformat: 1\n")
    assert [(f.code, f.lines) for f in notes.findings] == [("unknown-value", (2,))]
    assert "P1, P2, P3" in notes.findings[0].message


def test_a_value_equal_to_one_of_the_list_but_of_another_type_is_a_finding() -> None:
    assert found('name: x\nlevel: P1\nformat: "1"\n') == [("unknown-value", (3,))]
    assert found("name: x\nlevel: P1\nformat: true\n") == [("unknown-value", (3,))]
    assert found("name: x\nlevel: P1\nformat: 1.0\n") == [("unknown-value", (3,))]


def test_every_problem_of_a_mapping_is_noted() -> None:
    assert sorted(found("name: 3\nlevel: P9\ncolour: red\n")) == [
        ("missing-field", (1,)),
        ("unknown-field", (3,)),
        ("unknown-value", (2,)),
        ("wrong-type", (1,)),
    ]


def test_a_part_without_a_line_of_its_own_takes_the_line_of_what_contains_it() -> None:
    notes = Notes(read("a:\n  b: 1\n"))
    assert notes.line(("a", "b")) == 2
    assert notes.line(("a", "missing", "deeper")) == 1
    assert notes.line(("nowhere",)) == 1


def test_a_finding_may_be_about_several_lines_and_carry_another_verdict() -> None:
    notes = Notes(read("a: 1\n"))
    notes.add_at("duplicate-id", "the id 'x' appears 2 times", (3, 7), Verdict.ASK)
    notes.add("not-supported-yet", "not yet", ("a",), Verdict.ERROR)
    assert [(f.code, f.lines, f.verdict) for f in notes.findings] == [
        ("duplicate-id", (3, 7), Verdict.ASK),
        ("not-supported-yet", (1,), Verdict.ERROR),
    ]
