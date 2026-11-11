"""Duplicates and contradictions between the examples of a contract."""

from collections.abc import Mapping, Sequence
from itertools import combinations

from dokime.contract.expectations import Expected, holds, identical, is_exact
from dokime.contract.model import Example, Step
from dokime.core.findings import Finding
from dokime.core.verdicts import Verdict

_SPLIT_BY_NAME = ("files", "raises")


def compare(examples: Sequence[Example]) -> list[Finding]:
    """Find the pairs of examples that are the same or that cannot both hold.

    Two examples are compared when they have the same boundary and the same target.
    """
    findings = []
    for one, other in combinations(examples, 2):
        if (one.boundary, one.target) != (other.boundary, other.target):
            continue
        if _same_steps(one, other):
            findings.append(_finding("duplicate-example", "have the same steps", one, other))
        elif _contradict(one, other):
            reason = "expect what cannot both hold for the same inputs"
            findings.append(_finding("contradictory-examples", reason, one, other))
    return findings


def _finding(code: str, reason: str, one: Example, other: Example) -> Finding:
    message = f"the examples {one.id!r} and {other.id!r} {reason}"
    return Finding(code=code, message=message, verdict=Verdict.FAIL, lines=(one.line, other.line))


def _same_inputs(one: Step, other: Step) -> bool:
    return identical(dict(one.input), dict(other.input))


def _same_steps(one: Example, other: Example) -> bool:
    return len(one.steps) == len(other.steps) and all(
        _same_inputs(first, second) and identical(dict(first.expect), dict(second.expect))
        for first, second in zip(one.steps, other.steps, strict=True)
    )


def _contradict(one: Example, other: Example) -> bool:
    """Compare the steps from the first one, as long as their inputs are the same."""
    for first, second in zip(one.steps, other.steps, strict=False):
        if not _same_inputs(first, second):
            return False
        if _clash(_by_field(first.expect), _by_field(second.expect)):
            return True
    return False


def _by_field(expect: Mapping[str, Expected]) -> dict[str, Expected]:
    """Spread what a step expects into the fields that are compared one by one."""
    fields: dict[str, Expected] = {}
    for name, expected in expect.items():
        if name in _SPLIT_BY_NAME and isinstance(expected, dict):
            fields.update({f"{name}.{part}": inner for part, inner in expected.items()})
        else:
            fields[name] = expected
    return fields


def _clash(one: dict[str, Expected], other: dict[str, Expected]) -> bool:
    if _returns(one) != _returns(other) and _raises(one) != _raises(other):
        return True
    return any(_cannot_both_hold(one[name], other[name]) for name in one.keys() & other.keys())


def _returns(fields: dict[str, Expected]) -> bool:
    return "returns" in fields


def _raises(fields: dict[str, Expected]) -> bool:
    return any(name.startswith("raises.") for name in fields)


def _cannot_both_hold(one: Expected, other: Expected) -> bool:
    """Two exact values must be the same; an exact value must satisfy a matcher."""
    if is_exact(one) and is_exact(other):
        return not identical(one, other)
    if is_exact(one):
        return not holds(other, one)
    if is_exact(other):
        return not holds(one, other)
    return False
