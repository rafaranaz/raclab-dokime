"""A finding: one problem found by a check, with the verdict it gives."""

import re
from collections.abc import Iterable
from dataclasses import dataclass

from dokime.core.verdicts import Verdict, aggregate

_CODE = re.compile(r"[a-z]+(-[a-z]+)*")


@dataclass(frozen=True)
class Finding:
    """One problem found by a check.

    The code comes from a closed list and is made of lowercase words joined by hyphens. The lines
    are those of the file where the problem is, counted from 1; there may be none. The verdict is
    `FAIL`, `ASK` or `ERROR`: a finding is a reason against passing.
    """

    code: str
    message: str
    verdict: Verdict
    lines: tuple[int, ...] = ()

    def __post_init__(self) -> None:
        if not self.code:
            raise ValueError("a finding needs a code: it is empty")
        if not self.message:
            raise ValueError("a finding needs a message: it is empty")
        if not _CODE.fullmatch(self.code):
            raise ValueError(
                f"the code {self.code!r} is not made of lowercase words joined by hyphens"
            )
        if self.verdict is Verdict.PASS:
            raise ValueError(f"a finding cannot carry the verdict {self.verdict.value}")
        for line in self.lines:
            if line < 1:
                raise ValueError(f"the line {line} of a finding is smaller than 1")


def summarise(findings: Iterable[Finding]) -> Verdict:
    """Return the verdict that a list of findings gives: `PASS` when there are none."""
    verdicts = [finding.verdict for finding in findings]
    return aggregate(verdicts) if verdicts else Verdict.PASS
