"""The result of a gate."""

from dataclasses import dataclass

from dokime.core.findings import Finding, summarise
from dokime.core.verdicts import Verdict


@dataclass(frozen=True)
class GateResult:
    """What a gate gives: its name, and its findings, which decide its verdict."""

    gate: str
    findings: tuple[Finding, ...]

    @property
    def verdict(self) -> Verdict:
        """The summary of the findings: `PASS` when there are none."""
        return summarise(self.findings)
