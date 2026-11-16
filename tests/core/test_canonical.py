# SDD-EARS: CORE-100 CORE-101 CORE-102 CORE-103 CORE-104 CORE-105 CORE-106 CORE-107
"""The canonical form, with the vectors of sections 3.2.2 and 3.2.3 of RFC 8785.

Characters outside ASCII are built with `chr` so that this file says which code point it means.
"""

import hashlib
import json

import pytest

from dokime.core.canonical import NotCanonicalError, canonical, digest

LIMIT = 2**53 - 1
BACKSLASH, QUOTE = chr(0x5C), chr(0x22)
EURO, DALET, EMOJI = chr(0x20AC), chr(0xFB33), chr(0x1F600)


def test_there_is_no_space_between_the_parts() -> None:
    assert canonical({"a": [1, True, None], "b": {"c": "d"}}) == '{"a":[1,true,null],"b":{"c":"d"}}'


def test_the_keys_follow_the_example_of_section_3_2_3_of_rfc_8785() -> None:
    keys = {
        EURO: "Euro Sign",
        chr(0x0D): "Carriage Return",
        DALET: "Hebrew Letter Dalet With Dagesh",
        "1": "One",
        EMOJI: "Emoji: Grinning Face",
        chr(0x80): "Control",
        chr(0xF6): "Latin Small Letter O With Diaeresis",
    }
    assert list(json.loads(canonical(keys)).values()) == [
        "Carriage Return",
        "One",
        "Control",
        "Latin Small Letter O With Diaeresis",
        "Euro Sign",
        "Emoji: Grinning Face",
        "Hebrew Letter Dalet With Dagesh",
    ]


def test_a_character_outside_the_basic_plane_goes_before_one_inside_by_utf_16() -> None:
    assert canonical({DALET: 1, EMOJI: 2}) == "{" + f'"{EMOJI}":2,"{DALET}":1' + "}"


def test_a_text_follows_the_example_of_section_3_2_2_of_rfc_8785() -> None:
    given = EURO + "$" + chr(0x0F) + chr(0x0A) + "A'B" + QUOTE + BACKSLASH * 2 + QUOTE + "/"
    written = EURO + "$" + BACKSLASH + "u000f" + BACKSLASH + "nA'B"
    written += BACKSLASH + QUOTE + BACKSLASH * 4 + BACKSLASH + QUOTE + "/"
    assert canonical({"string": given}) == '{"string":"' + written + '"}'


@pytest.mark.parametrize(
    ("given", "written"),
    [
        (
            chr(8) + chr(9) + chr(10) + chr(12) + chr(13),
            BACKSLASH.join(["", "b", "t", "n", "f", "r"]),
        ),
        (chr(0) + chr(0x1F), BACKSLASH + "u0000" + BACKSLASH + "u001f"),
        (chr(0x7F) + chr(0xE9) + chr(0x2028), chr(0x7F) + chr(0xE9) + chr(0x2028)),
    ],
    ids=["short-escapes", "other-controls", "not-escaped"],
)
def test_only_the_quote_the_reverse_solidus_and_the_controls_are_escaped(
    given: str, written: str
) -> None:
    assert canonical(given) == QUOTE + written + QUOTE


@pytest.mark.parametrize(
    ("value", "place"),
    [(1.5, "the root"), ({"a": [0, 2.0]}, "a/1"), ({"a": float("nan")}, "a")],
)
def test_a_number_that_is_not_whole_is_refused_naming_its_place(value: object, place: str) -> None:
    with pytest.raises(NotCanonicalError, match=place):
        canonical(value)


@pytest.mark.parametrize("number", [LIMIT, -LIMIT])
def test_a_whole_number_at_the_limit_is_written(number: int) -> None:
    assert canonical([number]) == f"[{number}]"


@pytest.mark.parametrize("number", [LIMIT + 1, -LIMIT - 1, 10**30])
def test_a_whole_number_past_the_limit_is_refused_naming_its_place(number: int) -> None:
    with pytest.raises(NotCanonicalError, match="n/0"):
        canonical({"n": [number]})


@pytest.mark.parametrize(
    ("value", "place"),
    [({"a": "x" + chr(0xD800)}, "a"), ({chr(0xDC00): 1}, "the root"), ([chr(0xD83D)], "0")],
)
def test_a_lone_surrogate_is_refused_naming_its_place(value: object, place: str) -> None:
    with pytest.raises(NotCanonicalError, match=place):
        canonical(value)


@pytest.mark.parametrize(
    ("value", "place"),
    [({"a": b"x"}, "a"), ({1: "x"}, "the root"), ({"s": {1, 2}}, "s"), ([object()], "0")],
)
def test_anything_but_the_values_of_the_restriction_is_refused(value: object, place: str) -> None:
    with pytest.raises(NotCanonicalError, match=place):
        canonical(value)


def test_a_tuple_is_written_as_a_list() -> None:
    assert canonical(("a", 1)) == '["a",1]'


def test_the_digest_is_the_sha_256_of_the_canonical_form_in_utf_8() -> None:
    value = {"b": chr(0xE9), "a": 1}
    expected = hashlib.sha256(('{"a":1,"b":"' + chr(0xE9) + '"}').encode()).hexdigest()
    assert digest(value) == f"sha256:{expected}"
