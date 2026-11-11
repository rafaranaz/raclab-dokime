"""The findings of a check while it runs, with the line of the part each one is about."""

from dataclasses import dataclass, field

from dokime.core.findings import Finding
from dokime.core.reading import Path, Reading
from dokime.core.verdicts import Verdict


@dataclass
class Notes:
    """Collects findings and turns the path of a part of the contract into its line."""

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
