"""The check of a pack: it validates its text against the table of fields."""

import re
from collections.abc import Mapping
from pathlib import PurePosixPath

from dokime.core.reading import Value, read
from dokime.core.shape import Field, Notes, check_fields, one_of
from dokime.packs.model import Checked, Pack

_NAME = re.compile(r"[A-Za-z][A-Za-z0-9]*(-[A-Za-z0-9]+)*")


def _is_name(value: object) -> bool:
    return isinstance(value, str) and _NAME.fullmatch(value) is not None


def _is_line(value: object) -> bool:
    return isinstance(value, str) and value != "" and "\n" not in value


def _is_lines(value: object) -> bool:
    return isinstance(value, list) and all(_is_line(item) for item in value)


def _is_mapping(value: object) -> bool:
    return isinstance(value, dict)


_PACK: Mapping[str, Field] = {
    "format": one_of(1),
    "name": Field("a name: letters, digits and hyphens, starting with a letter", _is_name),
    "environment": Field("a mapping", _is_mapping),
    "tests": Field("a mapping", _is_mapping),
}
_ENVIRONMENT: Mapping[str, Field] = {"dockerfile": Field("a path of one line", _is_line)}
_TESTS: Mapping[str, Field] = {
    "command": Field("a list of texts: the command and its arguments", _is_lines),
    "report": Field("a path of one line", _is_line),
    "paths": Field("a list of patterns", _is_lines),
}


def check(text: str) -> Checked:
    """Check the text of a pack and return it together with every finding.

    Every finding comes in one result, in the order of the lines. The pack is returned when there
    is none.
    """
    reading = read(text)
    if reading.value is None:
        return Checked(pack=None, findings=reading.findings)
    notes = Notes(reading, list(reading.findings))
    pack = _pack(notes, reading.value)
    findings = tuple(sorted(notes.findings, key=lambda finding: (finding.lines, finding.code)))
    return Checked(pack=None if findings else pack, findings=findings)


def _pack(notes: Notes, root: Value) -> Pack | None:
    if not isinstance(root, dict):
        notes.add("wrong-type", "a pack is a mapping", ())
        return None
    check_fields(notes, root, (), _PACK)
    environment, tests = root.get("environment"), root.get("tests")
    if isinstance(environment, dict):
        check_fields(notes, environment, ("environment",), _ENVIRONMENT)
        _inside(notes, environment.get("dockerfile"), ("environment", "dockerfile"), "pack")
    if isinstance(tests, dict):
        check_fields(notes, tests, ("tests",), _TESTS)
        _inside(notes, tests.get("report"), ("tests", "report"), "output")
        for name in ("command", "paths"):
            if tests.get(name) == []:
                notes.add("empty-list", f"{name!r} has at least one item", ("tests", name))
        for pattern in _texts(tests.get("paths")):
            _inside(notes, pattern, ("tests", "paths"), "project")
    if notes.findings or not isinstance(environment, dict) or not isinstance(tests, dict):
        return None
    return Pack(
        name=str(root["name"]),
        dockerfile=str(environment["dockerfile"]),
        command=tuple(_texts(tests["command"])),
        report=str(tests["report"]),
        test_paths=tuple(_texts(tests["paths"])),
    )


def _texts(value: Value) -> list[str]:
    return [item for item in value if isinstance(item, str)] if isinstance(value, list) else []


def _inside(notes: Notes, path: Value, where: tuple[str, ...], limit: str) -> None:
    """Note a path that is absolute or that goes above the place it is relative to."""
    if not isinstance(path, str) or not _is_line(path):
        return
    parts = PurePosixPath(path).parts
    if path.startswith("/") or ".." in parts:
        message = f"{path!r} is not a path inside the {limit}: it is absolute or it has '..'"
        notes.add(f"path-outside-{limit}", message, where)
