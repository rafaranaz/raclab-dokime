"""The comparison of an example with what the zone observed of it (ADR-0012, ADR-0063).

Each step of the example is compared with the observation of the step in the same position, and
only in the parts that it expects; an expectation holds as `holds` of `contract` says. The type of
an exception is read as `pytest.raises` reads it, as the maintainer decided: a name without a
module is the class of that name in `builtins`, a name with one is the full name it gives, and it
holds when it is the full name of any class of the MRO observed, so `Exception` holds for any.
A `$repr` holds only for a value that JSON cannot hold whose `repr` was observed whole and is its
text; a difference says what the step did, never the `repr` observed (ADR-0079).
"""

from collections.abc import Mapping
from dataclasses import dataclass

from dokime.contract.expectations import Expected, Repr, holds
from dokime.contract.model import Example
from dokime.core.observation import (
    Ending,
    ExampleObservation,
    Exited,
    NotJson,
    Raised,
    Returned,
    StepObservation,
)

_CLI_PARTS = ("exit", "stdout", "stderr")


@dataclass(frozen=True)
class Difference:
    """A part of a step whose expectation does not hold, with what was expected and observed."""

    step: int
    part: str
    expected: object
    observed: object


@dataclass(frozen=True)
class Comparison:
    """The comparison of one example: it holds when it has no difference."""

    example: str
    differences: tuple[Difference, ...]

    @property
    def holds(self) -> bool:
        """Say whether every expectation of every step held."""
        return not self.differences


def compare(example: Example, observation: ExampleObservation) -> Comparison:
    """Compare an example of a contract with what the zone observed of it."""
    if observation.example != example.id:
        raise ValueError(
            f"the example {example.id!r} is compared with the observation of"
            f" {observation.example!r}"
        )
    differences: list[Difference] = []
    for position, step in enumerate(example.steps, start=1):
        if position > len(observation.steps):
            differences.append(Difference(position, "step", None, _why_not(observation)))
            continue
        seen = observation.steps[position - 1]
        if example.boundary == "cli":
            differences.extend(_cli(position, step.expect, seen))
        else:
            differences.extend(_function(position, step.expect, seen))
    return Comparison(example=example.id, differences=tuple(differences))


def _why_not(observation: ExampleObservation) -> str:
    """Why a step was not observed: the limit of time, or a crash with what is known of it."""
    if observation.ending is Ending.TIME_LIMIT:
        return "time-limit"
    if observation.signal is not None:
        return f"crashed by the signal {observation.signal}"
    if observation.exit_code is not None:
        return f"crashed with the exit code {observation.exit_code}"
    return "crashed"


def _said(seen: Returned | Raised | NotJson) -> str:
    """What a step at `function` did, in words, for a difference."""
    if isinstance(seen, Raised):
        return f"raised {seen.qualified}: {seen.message}"
    if isinstance(seen, NotJson):
        return f"returned a {seen.type}, which JSON cannot hold"
    return f"returned {seen.value!r}"


def _function(
    position: int, expect: Mapping[str, Expected], seen: StepObservation
) -> list[Difference]:
    if isinstance(seen, Exited):
        return [Difference(position, "boundary", "function", "cli")]
    if "returns" in expect:
        expected = expect["returns"]
        if isinstance(expected, Repr):
            return (
                []
                if _shown(expected, seen)
                else [Difference(position, "returns", expected, _said(seen))]
            )
        if not isinstance(seen, Returned):
            return [Difference(position, "returns", expected, _said(seen))]
        if not holds(expected, seen.value):
            return [Difference(position, "returns", expected, seen.value)]
    if "raises" in expect:
        expected = expect["raises"]
        if not isinstance(seen, Raised):
            return [Difference(position, "raises", expected, _said(seen))]
        if not _raised(expected, seen):
            return [Difference(position, "raises", expected, _said(seen))]
    return []


def _shown(expected: Repr, seen: StepObservation) -> bool:
    """Say whether a value that JSON cannot hold has the `repr` expected, observed whole."""
    return isinstance(seen, NotJson) and not seen.cut and seen.representation == expected.text


def _raised(expected: Expected, seen: Raised) -> bool:
    """Say whether an exception observed is the one expected, by its MRO and its message.

    The check of contracts makes the expectation a mapping with a `type`.
    """
    if not isinstance(expected, Mapping):
        raise TypeError(f"the expectation of an exception is a mapping, not {expected!r}")
    name = str(expected.get("type", ""))
    full = name if "." in name else f"builtins.{name}"
    if full not in seen.classes:
        return False
    return "message" not in expected or holds(expected["message"], seen.message)


def _cli(position: int, expect: Mapping[str, Expected], seen: StepObservation) -> list[Difference]:
    if not isinstance(seen, Exited):
        return [Difference(position, "boundary", "cli", "function")]
    observed: dict[str, object] = {"exit": seen.exit, "stdout": seen.stdout, "stderr": seen.stderr}
    differences = [
        Difference(position, part, expect[part], observed[part])
        for part in _CLI_PARTS
        if part in expect and not holds(expect[part], observed[part])
    ]
    files = expect.get("files")
    for name, expected in files.items() if isinstance(files, dict) else ():
        if name not in seen.files:
            differences.append(Difference(position, f"files/{name}", expected, "not written"))
        elif not holds(expected, seen.files[name]):
            differences.append(Difference(position, f"files/{name}", expected, seen.files[name]))
    return differences
