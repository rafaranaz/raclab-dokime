"""The result of a gate."""

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass

from dokime.core.findings import Finding, summarise
from dokime.core.verdicts import Verdict

ORIGINS = ("existing", "human", "derived", "model")
"""The origins of the checks, in the order a result lists them (ADR-0064)."""


@dataclass(frozen=True)
class Checks:
    """How many checks of one origin a gate ran."""

    origin: str
    total: int


def checks_of(origins: Iterable[str]) -> tuple[Checks, ...]:
    """The checks of a gate from the origin of each check it ran."""
    counted = Counter(origins)
    return tuple(Checks(origin, counted[origin]) for origin in ORIGINS if counted[origin])


@dataclass(frozen=True)
class GateResult:
    """What a gate gives: its name, its findings, which decide its verdict, the tests it left out
    as unstable, and its checks by origin."""

    gate: str
    findings: tuple[Finding, ...]
    unstable: tuple[str, ...] = ()
    """The tests whose outcome varied between the runs of the base, which the evidence lists."""
    checks: tuple[Checks, ...] = ()
    """One entry for each origin that has checks, in the order of `ORIGINS`."""

    def __post_init__(self) -> None:
        origins = [entry.origin for entry in self.checks]
        ordered = [origin for origin in ORIGINS if origin in origins]
        if origins != ordered or any(entry.total < 1 for entry in self.checks):
            raise ValueError(
                f"the checks {self.checks!r} are not one entry of at least one check for each"
                f" origin, in the order {', '.join(ORIGINS)}"
            )

    @property
    def verdict(self) -> Verdict:
        """The summary of the findings: `PASS` when there are none."""
        return summarise(self.findings)
