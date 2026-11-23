"""The reading of what the program that observes wrote, into the types of the port (ADR-0063).

The file was written inside the zone, where the code under test runs, so it is read as hostile:
opened without following a link, no more than its bytes and one, refusing repeated keys, `NaN`, the
infinities and a nesting deeper than 128 levels, and checked against the shape of the
observations and the examples that were requested. This reading is not the canonical form of
ADR-0062: a value returned may hold decimals.
"""

import json
import os
import stat
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any, NoReturn

from dokime.core.observation import (
    Ending,
    ExampleObservation,
    ExampleRequest,
    Exited,
    NotJson,
    Raised,
    Returned,
    StepObservation,
    not_json,
)
from dokime.core.repository import RefusalError

FILE = "observations.json"
DEPTH = 128


class _UnreadableError(Exception):
    """The observations do not have the shape they should."""


def _refuse(why: str) -> NoReturn:
    raise _UnreadableError(why)


def read_observations(
    output: Path, requests: tuple[ExampleRequest, ...], size: int
) -> tuple[ExampleObservation, ...]:
    """Read `observations.json` in the output directory, no more than `size` bytes."""
    data = _bytes(output, size)
    try:
        value = json.loads(data, object_pairs_hook=_no_repeated_key, parse_constant=_no_constant)
        _within_depth(value)
        return _examples(value, requests)
    except (ValueError, RecursionError, _UnreadableError) as error:
        raise RefusalError(
            "observations-unreadable", f"the observations cannot be read: {error}"
        ) from None


def _bytes(output: Path, size: int) -> bytes:
    try:
        descriptor = os.open(output / FILE, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    except FileNotFoundError:
        raise RefusalError("observations-missing", "the program wrote no observations") from None
    except OSError as error:
        raise RefusalError(
            "observations-unreadable", f"the observations cannot be opened: {error}"
        ) from None
    try:
        if not stat.S_ISREG(os.fstat(descriptor).st_mode):
            raise RefusalError("observations-unreadable", "the observations are not a file")
        with os.fdopen(descriptor, "rb", closefd=False) as handle:
            data = handle.read(size + 1)
    finally:
        os.close(descriptor)
    if len(data) > size:
        raise RefusalError(
            "observations-too-large", f"the observations are larger than {size} bytes"
        )
    return data


def _no_repeated_key(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    found: dict[str, Any] = {}
    for key, value in pairs:
        if key in found:
            _refuse(f"the key {key!r} is repeated")
        found[key] = value
    return found


def _no_constant(name: str) -> NoReturn:
    _refuse(f"{name} is not a value of JSON")


def _within_depth(value: object) -> None:
    waiting: list[tuple[object, int]] = [(value, 0)]
    while waiting:
        item, depth = waiting.pop()
        if isinstance(item, dict | list):
            if depth >= DEPTH:
                _refuse(f"the observations are nested more than {DEPTH} levels")
            children = item.values() if isinstance(item, dict) else item
            waiting.extend((child, depth + 1) for child in children)


def _field(mapping: object, name: str, kind: type | tuple[type, ...]) -> Any:
    if not isinstance(mapping, dict) or name not in mapping:
        _refuse(f"{name!r} is missing")
    value = mapping[name]
    if not isinstance(value, kind) or (isinstance(value, bool) and kind is int):
        _refuse(f"{name!r} is not of the right type")
    return value


def _examples(
    value: object, requests: tuple[ExampleRequest, ...]
) -> tuple[ExampleObservation, ...]:
    examples = _field(value, "examples", list)
    names = [_field(example, "example", str) for example in examples]
    if names != [request.example for request in requests]:
        _refuse(f"the observations are of {names}, not of the examples requested")
    return tuple(_example(example) for example in examples)


def _example(example: Mapping[str, Any]) -> ExampleObservation:
    try:
        ending = Ending(_field(example, "ending", str))
    except ValueError:
        _refuse(f"{example['ending']!r} is not an ending")
    signal = example.get("signal")
    exit_code = example.get("exit_code")
    for name, given in (("signal", signal), ("exit_code", exit_code)):
        if given is not None and (type(given) is not int):
            _refuse(f"{name!r} is not a whole number")
    steps = tuple(_step(step) for step in _field(example, "steps", list))
    try:
        return ExampleObservation(
            example=example["example"],
            steps=steps,
            ending=ending,
            signal=signal,
            exit_code=exit_code,
        )
    except ValueError as error:
        _refuse(str(error))


def _texts(value: object) -> dict[str, str]:
    if not isinstance(value, dict) or not all(isinstance(text, str) for text in value.values()):
        _refuse("the files are not texts by name")
    return dict(value)


_STEPS: Mapping[str, Callable[[Any], StepObservation]] = {
    "returned": lambda value: Returned(value=value),
    "not_json": lambda value: _not_json(value),
    "raised": lambda value: Raised(
        type=_field(value, "type", str),
        qualified=_field(value, "qualified", str),
        classes=tuple(_strings(_field(value, "classes", list))),
        message=_field(value, "message", str),
    ),
}


def _not_json(value: object) -> NotJson:
    """A value that JSON cannot hold: its type, and its `repr` within the limit of `core`."""
    if isinstance(value, str):
        return NotJson(type=value)
    kind = _field(value, "type", str)
    if not isinstance(value, dict) or "repr" not in value:
        return NotJson(type=kind)
    return not_json(kind, _field(value, "repr", str))


def _strings(values: list[Any]) -> list[str]:
    if not all(isinstance(value, str) for value in values):
        _refuse("the classes are not texts")
    return values


def _step(step: object) -> StepObservation:
    if isinstance(step, dict) and len(step) == 1:
        ((kind, value),) = step.items()
        if kind in _STEPS:
            return _STEPS[kind](value)
    if isinstance(step, dict) and set(step) == {"exit", "stdout", "stderr", "files"}:
        return Exited(
            exit=_field(step, "exit", int),
            stdout=_field(step, "stdout", str),
            stderr=_field(step, "stderr", str),
            files=_texts(step["files"]),
        )
    _refuse(f"{step!r} is not an observation of a step"[:200])
