"""A valid pack to seed defects into, and helpers to read the result of a check."""

from dokime.core.findings import Finding
from dokime.packs.check import check
from dokime.packs.model import Checked

VALID = """\
format: 1
name: cachetools
environment:
  dockerfile: Dockerfile
tests:
  command: [python, -m, pytest, --junitxml, /dokime/out/report.xml]
  report: report.xml
  paths: ["tests/**", "src/**/test_*.py"]
"""


def seeded(old: str, new: str) -> Checked:
    """Check the valid pack after replacing one piece of its text."""
    assert VALID.count(old) == 1, f"{old!r} appears {VALID.count(old)} times"
    return check(VALID.replace(old, new))


def line_of(piece: str) -> int:
    assert VALID.count(piece) == 1, f"{piece!r} appears {VALID.count(piece)} times"
    return VALID[: VALID.index(piece)].count("\n") + 1


def codes(checked: Checked) -> list[str]:
    return [finding.code for finding in checked.findings]


def only(checked: Checked, code: str) -> Finding:
    """The single finding of a check, which has to have this code."""
    assert codes(checked) == [code], [(f.code, f.lines, f.message) for f in checked.findings]
    return checked.findings[0]
