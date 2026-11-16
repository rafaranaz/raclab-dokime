"""The canonical form that digests are taken over (ADR-0062).

It is the JSON text of RFC 8785 restricted to the values of I-JSON without decimals: texts, whole
numbers, booleans, null, lists and mappings with text keys. With no decimals, the numbers of
ECMAScript reduce to the whole numbers that Python writes, and what is left of RFC 8785 is the
order of the keys, by UTF-16 code units, and the escapes of a text.
"""

import hashlib
import json
from collections.abc import Mapping, Sequence

LIMIT = 2**53 - 1
"""The largest whole number of I-JSON, RFC 7493: the numbers of a double that are exact."""

DEPTH = 128
"""How many lists and mappings deep a value may be: a deeper one is refused, not overflowed."""

_SURROGATES = range(0xD800, 0xE000)

type Place = tuple[str | int, ...]


class NotCanonicalError(ValueError):
    """A value that the canonical form refuses, with the place of the part that it refuses."""


def canonical(value: object) -> str:
    """Give the canonical form of a value."""
    return "".join(_write(value, ()))


def digest(value: object) -> str:
    """Give the digest of a value: `sha256:` and the SHA-256 of its canonical form in UTF-8."""
    return "sha256:" + hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def _named(place: Place) -> str:
    return "/".join(str(part) for part in place) if place else "the root"


def _refuse(place: Place, why: str) -> NotCanonicalError:
    return NotCanonicalError(f"the value at {_named(place)} {why}")


def _text(text: str, place: Place) -> str:
    if any(ord(character) in _SURROGATES for character in text):
        raise _refuse(place, "holds a lone surrogate of UTF-16")
    return json.dumps(text, ensure_ascii=False)


def _write(value: object, place: Place) -> list[str]:
    if value is None or isinstance(value, bool):
        return [json.dumps(value)]
    if isinstance(value, int):
        if not -LIMIT <= value <= LIMIT:
            raise _refuse(place, f"is a whole number outside ±{LIMIT}")
        return [str(value)]
    if isinstance(value, float):
        raise _refuse(place, "is a number that is not whole")
    if isinstance(value, str):
        return [_text(value, place)]
    container = isinstance(value, Mapping) or (
        isinstance(value, Sequence) and not isinstance(value, bytes | bytearray)
    )
    if container and len(place) >= DEPTH:
        raise _refuse(place, f"is nested more than {DEPTH} levels deep")
    if isinstance(value, Mapping):
        return _mapping(value, place)
    if isinstance(value, Sequence) and not isinstance(value, bytes | bytearray):
        parts = [_write(item, (*place, index)) for index, item in enumerate(value)]
        return ["[", ",".join("".join(part) for part in parts), "]"]
    raise _refuse(place, f"is a {type(value).__name__}, which JSON does not hold")


def _mapping(value: Mapping[object, object], place: Place) -> list[str]:
    for key in value:
        if not isinstance(key, str):
            raise _refuse(place, f"has the key {key!r}, which is not a text")
        _text(key, place)
    keys = sorted(value, key=lambda key: str(key).encode("utf-16-be"))
    members = [
        _text(str(key), place) + ":" + "".join(_write(value[key], (*place, str(key))))
        for key in keys
    ]
    return ["{", ",".join(members), "}"]
