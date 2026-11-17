"""Whether the section of a mixed file changed between two versions of the file (ADR-0059).

pytest reads an INI file with `iniconfig`, not with `configparser`, and the two differ in
interpolation, comments at the end of a line, repeated keys and case; so a section of the format
`ini` is compared by its text, and any byte changed in it is a change. A section of the format
`toml` is compared by the value that `tomllib` reads at its dotted path, since TOML can define the
same table with dotted keys elsewhere in the file. A version that cannot be read counts as changed.
"""

import tomllib

from dokime.packs.model import Section

_UNREADABLE = object()


def section_changed(section: Section, before: bytes | None, after: bytes | None) -> bool:
    """Say whether the section differs between two versions of its file; `None` is no file."""
    read = _toml if section.format == "toml" else _ini
    old, new = read(section.name, before), read(section.name, after)
    return old is _UNREADABLE or new is _UNREADABLE or old != new


def _text(data: bytes) -> str | object:
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return _UNREADABLE


def _ini(name: str, data: bytes | None) -> object:
    """Every occurrence of the section, its header and its lines up to the next header."""
    if data is None:
        return ()
    text = _text(data)
    if not isinstance(text, str):
        return _UNREADABLE
    found: list[str] = []
    inside = False
    for line in text.splitlines(keepends=True):
        if line.startswith("["):
            inside = line[1:].split("]", 1)[0].strip() == name
        if inside:
            found.append(line)
    return tuple(found)


def _toml(name: str, data: bytes | None) -> object:
    """The value at the dotted path of the section, or `None` when the path is absent."""
    if data is None:
        return None
    text = _text(data)
    if not isinstance(text, str):
        return _UNREADABLE
    try:
        value: object = tomllib.loads(text)
    except tomllib.TOMLDecodeError:
        return _UNREADABLE
    for key in name.split("."):
        if not isinstance(value, dict) or key not in value:
            return None
        value = value[key]
    return value
