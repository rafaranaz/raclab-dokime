"""The shape of what was read: the fields each mapping may have and what they hold."""

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field

from dokime.core.findings import Finding
from dokime.core.reading import Path, Reading
from dokime.core.verdicts import Verdict


@dataclass(frozen=True)
class Field:
    """What a field holds, and whether its mapping has to have it.

    A field with `allowed` values holds one of them; any other holds what `fits` accepts.
    """

    holds: str
    fits: Callable[[object], bool] | None = None
    allowed: tuple[object, ...] = ()
    mandatory: bool = True


def one_of(*values: object, mandatory: bool = True) -> Field:
    """A field that holds one of a closed list of values."""
    return Field(", ".join(str(value) for value in values), allowed=values, mandatory=mandatory)


@dataclass
class Notes:
    """Collects the findings of a check and turns the path of a part into its line."""

    reading: Reading
    findings: list[Finding] = field(default_factory=list)

    def line(self, path: Path) -> int:
        """The line of a part, or of the nearest part that contains it."""
        while path and path not in self.reading.lines:
            path = path[:-1]
        return self.reading.lines.get(path, 1)

    def add(self, code: str, message: str, path: Path, verdict: Verdict = Verdict.FAIL) -> None:
        """Note a finding about the part at a path."""
        self.add_at(code, message, (self.line(path),), verdict)

    def add_at(
        self, code: str, message: str, lines: tuple[int, ...], verdict: Verdict = Verdict.FAIL
    ) -> None:
        """Note a finding about several lines."""
        self.findings.append(Finding(code=code, message=message, verdict=verdict, lines=lines))


def check_fields(
    notes: Notes, mapping: Mapping[str, object], path: Path, table: Mapping[str, Field]
) -> None:
    """Note the fields of a mapping that its table does not list, lacks or states otherwise."""
    for name in mapping:
        if name not in table:
            listed = ", ".join(table)
            message = f"{name!r} is not a field here; they are {listed}"
            notes.add("unknown-field", message, (*path, name))
    for name, expected in table.items():
        if name not in mapping:
            if expected.mandatory:
                notes.add("missing-field", f"the field {name!r} is missing", path)
        elif expected.fits is None:
            if not _is_allowed(mapping[name], expected.allowed):
                notes.add("unknown-value", f"{name!r} is one of: {expected.holds}", (*path, name))
        elif not expected.fits(mapping[name]):
            notes.add("wrong-type", f"{name!r} holds {expected.holds}", (*path, name))


def _is_allowed(value: object, allowed: tuple[object, ...]) -> bool:
    """A value is allowed when it equals one of the list and has its type: 1 is not true."""
    return any(type(value) is type(one) and value == one for one in allowed)
