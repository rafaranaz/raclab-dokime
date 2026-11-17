"""The result of a gate."""

from dataclasses import dataclass

from dokime.core.findings import Finding, summarise
from dokime.core.verdicts import Verdict


@dataclass(frozen=True)
class GateResult:
    """What a gate gives: its name, its findings, which decide its verdict, and the tests it left
    out as unstable."""

    gate: str
    findings: tuple[Finding, ...]
    unstable: tuple[str, ...] = ()
    """The tests whose outcome varied between the runs of the base, which the evidence lists."""

    @property
    def verdict(self) -> Verdict:
        """The summary of the findings: `PASS` when there are none."""
        return summarise(self.findings)
