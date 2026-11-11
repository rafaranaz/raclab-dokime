"""What an example expects, and when an expectation holds for what was observed."""

import json
import re
from dataclasses import dataclass
from datetime import datetime
from typing import TypeIs


@dataclass(frozen=True)
class Contains:
    """The observed text contains this text."""

    text: str


@dataclass(frozen=True)
class FullMatch:
    """This regular expression matches the observed text from its first character to its last."""

    pattern: str


@dataclass(frozen=True)
class Approx:
    """The observed number differs from this one by no more than the tolerance."""

    number: float
    tolerance: float


@dataclass(frozen=True)
class Unordered:
    """The observed list has these items, in any order."""

    items: tuple["Expected", ...]


@dataclass(frozen=True)
class AnyValue:
    """The observed text is of this kind: `uuid` or `timestamp`."""

    kind: str


@dataclass(frozen=True)
class Json:
    """The observed text is JSON whose value satisfies this expectation."""

    value: "Expected"


type Matcher = Contains | FullMatch | Approx | Unordered | AnyValue | Json
type Expected = bool | int | float | str | list[Expected] | dict[str, Expected] | Matcher | None


_UUID = re.compile(r"[0-9a-fA-F]{8}(-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}")
_TIMESTAMP = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})?")


def holds(expected: Expected, observed: object) -> bool:
    """Say whether an expectation holds for an observed value.

    An exact value holds for an equal value of the same type, so 1 is neither 1.0 nor true.
    """
    if isinstance(expected, dict):
        return (
            isinstance(observed, dict)
            and expected.keys() == observed.keys()
            and all(holds(value, observed[key]) for key, value in expected.items())
        )
    if isinstance(expected, list):
        return (
            isinstance(observed, list)
            and len(expected) == len(observed)
            and all(holds(item, seen) for item, seen in zip(expected, observed, strict=True))
        )
    if isinstance(expected, Unordered):
        return isinstance(observed, list) and _pairs(list(expected.items), observed)
    if isinstance(expected, Json):
        return _holds_as_json(expected.value, observed)
    if isinstance(expected, Approx):
        return _is_number(observed) and abs(observed - expected.number) <= expected.tolerance
    if isinstance(expected, Contains | FullMatch | AnyValue):
        return isinstance(observed, str) and _holds_for_text(expected, observed)
    return type(expected) is type(observed) and expected == observed


def is_exact(expected: Expected) -> bool:
    """Say whether an expectation is an exact value, with no matcher anywhere inside it."""
    if isinstance(expected, dict):
        return all(is_exact(value) for value in expected.values())
    if isinstance(expected, list):
        return all(is_exact(item) for item in expected)
    return not isinstance(expected, Contains | FullMatch | Approx | Unordered | AnyValue | Json)


def identical(one: Expected, other: Expected) -> bool:
    """Say whether two expectations, or two inputs, are written the same, types included."""
    if type(one) is not type(other):
        return False
    if isinstance(one, dict) and isinstance(other, dict):
        return one.keys() == other.keys() and all(identical(one[key], other[key]) for key in one)
    if isinstance(one, list) and isinstance(other, list):
        return len(one) == len(other) and all(map(identical, one, other))
    if isinstance(one, Unordered) and isinstance(other, Unordered):
        return identical(list(one.items), list(other.items))
    if isinstance(one, Json) and isinstance(other, Json):
        return identical(one.value, other.value)
    return one == other


def _is_number(observed: object) -> TypeIs[int | float]:
    return isinstance(observed, int | float) and not isinstance(observed, bool)


def _holds_for_text(expected: Contains | FullMatch | AnyValue, observed: str) -> bool:
    if isinstance(expected, Contains):
        return expected.text in observed
    if isinstance(expected, FullMatch):
        return re.fullmatch(expected.pattern, observed) is not None
    if expected.kind == "uuid":
        return _UUID.fullmatch(observed) is not None
    return _TIMESTAMP.fullmatch(observed) is not None and _is_a_real_moment(observed)


def _is_a_real_moment(text: str) -> bool:
    try:
        datetime.fromisoformat(text)
    except ValueError:
        return False
    return True


def _holds_as_json(expected: Expected, observed: object) -> bool:
    if not isinstance(observed, str):
        return False
    try:
        value = json.loads(observed)
    except ValueError:
        return False
    return holds(expected, value)


def _pairs(expected: list[Expected], observed: list[object]) -> bool:
    """Say whether each expected item can be paired with a different observed item."""
    if len(expected) != len(observed):
        return False
    if not expected:
        return True
    first, rest = expected[0], expected[1:]
    return any(
        holds(first, seen) and _pairs(rest, observed[:index] + observed[index + 1 :])
        for index, seen in enumerate(observed)
    )
