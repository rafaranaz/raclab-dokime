"""The directives of a contract: mappings with a key that starts with `$`."""

import json
import re
from collections.abc import Callable
from dataclasses import dataclass
from typing import cast

from dokime.contract.expectations import (
    AnyValue,
    Approx,
    Contains,
    Expected,
    FullMatch,
    Json,
    Unordered,
)
from dokime.contract.notes import Notes
from dokime.core.reading import Path, Value
from dokime.core.verdicts import Verdict

type _Build = Callable[["Resolver", dict[str, Value], Path, bool], Expected]


@dataclass(frozen=True)
class _Directive:
    build: _Build
    matcher: bool = True
    parameters: tuple[str, ...] = ()


@dataclass
class Resolver:
    """Turns what is written in an input or an expectation into what it means."""

    notes: Notes

    def resolve(self, value: Value, path: Path, in_expectation: bool) -> Expected:
        """Read the directives of a value. A problem is noted and gives nothing."""
        if isinstance(value, list):
            return [
                self.resolve(item, (*path, index), in_expectation)
                for index, item in enumerate(value)
            ]
        if not isinstance(value, dict):
            return value
        names = [key for key in value if key.startswith("$")]
        if not names:
            return {
                key: self.resolve(item, (*path, key), in_expectation) for key, item in value.items()
            }
        if len(names) > 1:
            message = f"a mapping has one directive at most; this one has {', '.join(names)}"
            self.notes.add("several-directives", message, path)
            return None
        return self._directive(names[0], value, path, in_expectation)

    def _directive(
        self, name: str, mapping: dict[str, Value], path: Path, in_expectation: bool
    ) -> Expected:
        if name == "$ref":
            message = "the matcher $ref is not supported in this version"
            self.notes.add("not-supported-yet", message, path, Verdict.ERROR)
            return None
        directive = _DIRECTIVES.get(name)
        if directive is None:
            known = ", ".join(_DIRECTIVES)
            self.notes.add(
                "unknown-directive", f"{name} is not a directive; they are {known}", path
            )
            return None
        if not self._parameters_fit(name, directive, mapping, path):
            return None
        if directive.matcher and not in_expectation:
            message = f"the matcher {name} is in an input; a matcher belongs in an expectation"
            self.notes.add("matcher-in-input", message, path)
            return None
        return directive.build(self, mapping, path, in_expectation)

    def _parameters_fit(
        self, name: str, directive: _Directive, mapping: dict[str, Value], path: Path
    ) -> bool:
        given = [key for key in mapping if key != name]
        for parameter in given:
            if parameter not in directive.parameters:
                message = f"{name} has no parameter {parameter!r}"
                self.notes.add("directive-parameter", message, (*path, parameter))
                return False
        for parameter in directive.parameters:
            if parameter not in given:
                message = f"{name} needs the parameter {parameter!r}"
                self.notes.add("directive-parameter", message, path)
                return False
        return True

    def wrong_value(self, name: str, holds: str, path: Path) -> Expected:
        """Note that the value of a directive, or of its parameter, is not what it holds."""
        self.notes.add("directive-value", f"{name} holds {holds}", path)
        return None


def _text(resolver: Resolver, mapping: dict[str, Value], path: Path, _: bool) -> Expected:
    text, final_newline = mapping["$text"], mapping["final_newline"]
    if not isinstance(text, str) or (*path, "$text") not in resolver.notes.reading.blocks:
        return resolver.wrong_value("$text", "a literal block (|)", (*path, "$text"))
    if not isinstance(final_newline, bool):
        return resolver.wrong_value("final_newline", "true or false", (*path, "final_newline"))
    return text if final_newline else text.removesuffix("\n")


def _literal(_: Resolver, mapping: dict[str, Value], __: Path, ___: bool) -> Expected:
    return cast(Expected, mapping["$literal"])


def _json(
    resolver: Resolver, mapping: dict[str, Value], path: Path, in_expectation: bool
) -> Expected:
    value = resolver.resolve(mapping["$json"], (*path, "$json"), in_expectation)
    return Json(value) if in_expectation else json.dumps(value, ensure_ascii=False)


def _contains(resolver: Resolver, mapping: dict[str, Value], path: Path, _: bool) -> Expected:
    text = mapping["$contains"]
    if not isinstance(text, str):
        return resolver.wrong_value("$contains", "a text", path)
    return Contains(text)


def _fullmatch(resolver: Resolver, mapping: dict[str, Value], path: Path, _: bool) -> Expected:
    pattern = mapping["$fullmatch"]
    if not isinstance(pattern, str) or not _compiles(pattern):
        return resolver.wrong_value("$fullmatch", "a regular expression of Python", path)
    return FullMatch(pattern)


def _compiles(pattern: str) -> bool:
    try:
        re.compile(pattern)
    except re.error:
        return False
    return True


def _is_number(value: Value) -> bool:
    return isinstance(value, int | float) and not isinstance(value, bool)


def _approx(resolver: Resolver, mapping: dict[str, Value], path: Path, _: bool) -> Expected:
    number, tolerance = mapping["$approx"], mapping["tolerance"]
    if not isinstance(number, int | float) or not _is_number(number):
        return resolver.wrong_value("$approx", "a number", path)
    if not isinstance(tolerance, int | float) or not _is_number(tolerance) or tolerance < 0:
        return resolver.wrong_value(
            "tolerance", "a number that is not negative", (*path, "tolerance")
        )
    return Approx(float(number), float(tolerance))


def _unordered(resolver: Resolver, mapping: dict[str, Value], path: Path, _: bool) -> Expected:
    items = mapping["$unordered"]
    if not isinstance(items, list):
        return resolver.wrong_value("$unordered", "a list", path)
    return Unordered(
        tuple(
            resolver.resolve(item, (*path, "$unordered", index), True)
            for index, item in enumerate(items)
        )
    )


def _any(resolver: Resolver, mapping: dict[str, Value], path: Path, _: bool) -> Expected:
    kind = mapping["$any"]
    if kind not in ("uuid", "timestamp") or not isinstance(kind, str):
        return resolver.wrong_value("$any", "uuid or timestamp", path)
    return AnyValue(kind)


_DIRECTIVES: dict[str, _Directive] = {
    "$text": _Directive(_text, matcher=False, parameters=("final_newline",)),
    "$json": _Directive(_json, matcher=False),
    "$literal": _Directive(_literal, matcher=False),
    "$contains": _Directive(_contains),
    "$fullmatch": _Directive(_fullmatch),
    "$approx": _Directive(_approx, parameters=("tolerance",)),
    "$unordered": _Directive(_unordered),
    "$any": _Directive(_any),
}
