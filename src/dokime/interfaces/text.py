"""How a command writes its findings and its verdict, and the exit code of each verdict."""

from collections.abc import Sequence

from dokime.core.findings import Finding
from dokime.core.verdicts import Verdict

EXIT_CODES = {Verdict.PASS: 0, Verdict.FAIL: 1, Verdict.ERROR: 2, Verdict.ASK: 3}
_COUNTED = (Verdict.FAIL, Verdict.ASK, Verdict.ERROR)


def finding_line(path: str, finding: Finding) -> str:
    """A finding as `path:line: VERDICT code: message`, or `path: ...` when it has no line."""
    place = f"{path}:{finding.lines[0]}" if finding.lines else path
    others = finding.lines[1:]
    also = ""
    if others:
        word = "lines" if len(others) > 1 else "line"
        also = f" (also {word} {', '.join(str(line) for line in others)})"
    return f"{place}: {finding.verdict.value} {finding.code}: {finding.message}{also}"


def summary(verdict: Verdict, findings: Sequence[Finding]) -> str:
    """The last line: the verdict and how many findings there are of each verdict."""
    total = len(findings)
    if not total:
        return f"{verdict.value}: no findings"
    counts = [
        f"{count} {counted.value.lower()}"
        for counted in _COUNTED
        if (count := sum(finding.verdict is counted for finding in findings))
    ]
    noun = "finding" if total == 1 else "findings"
    return f"{verdict.value}: {total} {noun} ({', '.join(counts)})"
