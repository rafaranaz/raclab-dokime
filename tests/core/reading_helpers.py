"""Helpers of the tests of the strict reader."""

from dokime.core.reading import Reading


def codes(reading: Reading) -> list[str]:
    return [finding.code for finding in reading.findings]


def lines_of(reading: Reading, code: str) -> list[tuple[int, ...]]:
    return [finding.lines for finding in reading.findings if finding.code == code]
