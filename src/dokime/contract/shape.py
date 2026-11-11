"""The shape of a contract: which fields each of its mappings may have and what they hold."""

import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass

from dokime.contract import ears
from dokime.contract.directives import Resolver
from dokime.contract.expectations import AnyValue, Contains, Expected, FullMatch, Json
from dokime.contract.model import Example, Relation, Requirement, Step
from dokime.contract.notes import Notes
from dokime.core.reading import Path, Value
from dokime.core.verdicts import Verdict

_NAME = re.compile(r"[A-Za-z][A-Za-z0-9]*(-[A-Za-z0-9]+)*")
_FUNCTION = re.compile(r"[A-Za-z_][\w.]*:[A-Za-z_]\w*")
_EXCEPTION = re.compile(r"[A-Za-z_][\w.]*")
KINDS = ("new", "change", "preserve")
BOUNDARIES = ("function", "cli", "http")
RELATIONS = ("idempotent", "order-insensitive")


@dataclass(frozen=True)
class Field:
    """What a field holds, and whether its mapping has to have it."""

    holds: str
    fits: Callable[[object], bool] | None = None
    allowed: tuple[object, ...] = ()
    mandatory: bool = True


def is_name(value: object) -> bool:
    return isinstance(value, str) and _NAME.fullmatch(value) is not None


def _is_line(value: object) -> bool:
    return isinstance(value, str) and value != "" and "\n" not in value


def _is_text(value: object) -> bool:
    return isinstance(value, str)


def _is_integer(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _is_list(value: object) -> bool:
    return isinstance(value, list)


def _is_mapping(value: object) -> bool:
    return isinstance(value, dict)


def _is_texts(value: object) -> bool:
    return isinstance(value, list) and all(isinstance(item, str) for item in value)


def _is_text_or_matcher(value: object) -> bool:
    return isinstance(value, str | Contains | FullMatch | AnyValue | Json)


def _is_texts_by_name(value: object) -> bool:
    return isinstance(value, dict) and all(isinstance(item, str) for item in value.values())


def _is_expected_files(value: object) -> bool:
    return isinstance(value, dict) and all(_is_text_or_matcher(item) for item in value.values())


def _is_raises(value: object) -> bool:
    return (
        isinstance(value, dict)
        and set(value) <= {"type", "message"}
        and isinstance(value.get("type"), str)
        and _EXCEPTION.fullmatch(value["type"]) is not None
        and ("message" not in value or _is_text_or_matcher(value["message"]))
    )


def _anything(_: object) -> bool:
    return True


def _one_of(*values: object, mandatory: bool = True) -> Field:
    return Field(", ".join(str(value) for value in values), allowed=values, mandatory=mandatory)


_A_NAME = Field("a name: letters, digits and hyphens, starting with a letter", is_name)
_A_LINE = Field("a text of one line", _is_line)
_A_LINE_IF_ANY = Field("a text of one line", _is_line, mandatory=False)

CONTRACT: Mapping[str, Field] = {
    "format": _one_of(1),
    "story": _A_NAME,
    "may_modify_tests": Field("a list of texts", _is_texts, mandatory=False),
    "requirements": Field("a list of requirements", _is_list),
    "examples": Field("a list of examples", _is_list),
    "relations": Field("a list of relations", _is_list, mandatory=False),
}
_REQUIREMENT: Mapping[str, Field] = {
    "id": _A_NAME,
    "kind": _one_of(*KINDS),
    "text": _A_LINE,
    "source": _one_of("written", "imported"),
    "replaces": _A_LINE_IF_ANY,
}
_EXAMPLE: Mapping[str, Field] = {
    "id": _A_NAME,
    "requirement": _A_NAME,
    "case": _A_NAME,
    "boundary": _one_of(*BOUNDARIES),
    "target": _A_LINE,
    "description": _A_LINE_IF_ANY,
    "origin": _one_of("human", "model"),
    "steps": Field("a list of steps", _is_list),
}
_STEP: Mapping[str, Field] = {
    "input": Field("a mapping", _is_mapping),
    "expect": Field("a mapping", _is_mapping),
}
_INPUT: Mapping[str, Mapping[str, Field]] = {
    "function": {
        "args": Field("a list of values", _is_list, mandatory=False),
        "kwargs": Field("a mapping of values", _is_mapping, mandatory=False),
    },
    "cli": {
        "args": Field("a list of texts", _is_texts, mandatory=False),
        "stdin": Field("a text", _is_text, mandatory=False),
        "files": Field("a mapping from a file name to a text", _is_texts_by_name, mandatory=False),
        "env": Field("a mapping from a name to a text", _is_texts_by_name, mandatory=False),
    },
}
_EXPECT: Mapping[str, Mapping[str, Field]] = {
    "function": {
        "returns": Field("a value", _anything, mandatory=False),
        "raises": Field(
            "a mapping with 'type', the name of the exception, and optionally 'message'",
            _is_raises,
            mandatory=False,
        ),
    },
    "cli": {
        "exit": Field("an integer", _is_integer, mandatory=False),
        "stdout": Field("a text or a matcher of texts", _is_text_or_matcher, mandatory=False),
        "stderr": Field("a text or a matcher of texts", _is_text_or_matcher, mandatory=False),
        "files": Field(
            "a mapping from a file name to a text or a matcher of texts",
            _is_expected_files,
            mandatory=False,
        ),
    },
}
_RELATION: Mapping[str, Field] = {
    "id": _A_NAME,
    "requirement": _A_NAME,
    "relation": _one_of(*RELATIONS),
    "target": _A_LINE,
}
_OVER: Mapping[str, Field] = {"over": _A_LINE}
_OVER_IF_ANY: Mapping[str, Field] = {"over": _A_LINE_IF_ANY}


def _is_allowed(value: object, allowed: tuple[object, ...]) -> bool:
    return any(type(value) is type(one) and value == one for one in allowed)


def check_fields(
    notes: Notes, mapping: Mapping[str, object], path: Path, table: Mapping[str, Field]
) -> None:
    """Note the fields of a mapping that its table does not list, lacks or states otherwise."""
    for name in mapping:
        if name not in table:
            listed = ", ".join(table)
            notes.add(
                "unknown-field", f"{name!r} is not a field here; they are {listed}", (*path, name)
            )
    for name, field in table.items():
        if name not in mapping:
            if field.mandatory:
                notes.add("missing-field", f"the field {name!r} is missing", path)
        elif field.fits is None:
            if not _is_allowed(mapping[name], field.allowed):
                notes.add("unknown-value", f"{name!r} is one of: {field.holds}", (*path, name))
        elif not field.fits(mapping[name]):
            notes.add("wrong-type", f"{name!r} holds {field.holds}", (*path, name))


def _mapping(notes: Notes, item: Value, path: Path, what: str) -> dict[str, Value] | None:
    if isinstance(item, dict):
        return item
    notes.add("wrong-type", f"{what} is a mapping", path)
    return None


def requirement(notes: Notes, item: Value, path: Path) -> Requirement | None:
    """Check one requirement and return it when it has no finding."""
    before = len(notes.findings)
    fields = _mapping(notes, item, path, "a requirement")
    if fields is None:
        return None
    check_fields(notes, fields, path, _REQUIREMENT)
    text, kind = fields.get("text"), fields.get("kind")
    if isinstance(text, str) and _is_line(text) and (why := ears.problem(text)):
        message = f"the text of the requirement {fields.get('id')!r} is not EARS: {why}"
        notes.add("not-ears", message, (*path, "text"))
    if "replaces" in fields and kind in ("new", "preserve"):
        message = f"'replaces' belongs to a requirement of kind change; this one is {kind}"
        notes.add("replaces-without-change", message, (*path, "replaces"))
    if len(notes.findings) > before:
        return None
    replaces = fields.get("replaces")
    return Requirement(
        id=str(fields["id"]),
        kind=str(kind),
        text=str(text),
        source=str(fields["source"]),
        replaces=replaces if isinstance(replaces, str) else None,
        line=notes.line(path),
    )


def relation(notes: Notes, item: Value, path: Path) -> Relation | None:
    """Check one relation and return it when it has no finding."""
    before = len(notes.findings)
    fields = _mapping(notes, item, path, "a relation")
    if fields is None:
        return None
    name = fields.get("relation")
    over = {"idempotent": {}, "order-insensitive": _OVER}.get(str(name), _OVER_IF_ANY)
    check_fields(notes, fields, path, {**_RELATION, **over})
    if len(notes.findings) > before:
        return None
    given = fields.get("over")
    return Relation(
        id=str(fields["id"]),
        requirement=str(fields["requirement"]),
        relation=str(name),
        target=str(fields["target"]),
        over=given if isinstance(given, str) else None,
        line=notes.line(path),
    )


def example(notes: Notes, item: Value, path: Path) -> Example | None:
    """Check one example and return it when it has no finding."""
    before = len(notes.findings)
    fields = _mapping(notes, item, path, "an example")
    if fields is None:
        return None
    check_fields(notes, fields, path, _EXAMPLE)
    boundary, target, steps = fields.get("boundary"), fields.get("target"), fields.get("steps")
    if boundary == "http":
        message = "examples at the http boundary are not supported in this version"
        notes.add("not-supported-yet", message, (*path, "boundary"), Verdict.ERROR)
        return None
    checked: list[Step | None] = []
    if isinstance(boundary, str) and boundary in _INPUT and isinstance(steps, list):
        if boundary == "function" and _is_line(target) and not _FUNCTION.fullmatch(str(target)):
            message = "'target' at the function boundary is written module:function"
            notes.add("wrong-type", message, (*path, "target"))
        if not steps:
            notes.add("empty-list", "an example has at least one step", (*path, "steps"))
        checked = [
            _step(notes, step, (*path, "steps", index), boundary)
            for index, step in enumerate(steps)
        ]
    if len(notes.findings) > before:
        return None
    description = fields.get("description")
    return Example(
        id=str(fields["id"]),
        requirement=str(fields["requirement"]),
        case=str(fields["case"]),
        boundary=str(boundary),
        target=str(target),
        description=description if isinstance(description, str) else None,
        origin=str(fields["origin"]),
        steps=tuple(step for step in checked if step is not None),
        line=notes.line(path),
    )


def _step(notes: Notes, item: Value, path: Path, boundary: str) -> Step | None:
    fields = _mapping(notes, item, path, "a step")
    if fields is None:
        return None
    check_fields(notes, fields, path, _STEP)
    given, expected = fields.get("input"), fields.get("expect")
    if not isinstance(given, dict) or not isinstance(expected, dict):
        return None
    before = len(notes.findings)
    resolver = Resolver(notes)
    inputs: dict[str, Expected] = {
        key: resolver.resolve(value, (*path, "input", key), False) for key, value in given.items()
    }
    expects: dict[str, Expected] = {
        key: resolver.resolve(value, (*path, "expect", key), True)
        for key, value in expected.items()
    }
    if len(notes.findings) > before:
        return None
    check_fields(notes, inputs, (*path, "input"), _INPUT[boundary])
    check_fields(notes, expects, (*path, "expect"), _EXPECT[boundary])
    declared = [name for name in _EXPECT[boundary] if name in expects]
    if not declared:
        notes.add("no-expectation", "a step expects at least one thing", (*path, "expect"))
    if "returns" in expects and "raises" in expects:
        message = "a step expects 'returns' or 'raises', not both"
        notes.add("two-expectations", message, (*path, "expect"))
    return Step(input=inputs, expect=expects)
