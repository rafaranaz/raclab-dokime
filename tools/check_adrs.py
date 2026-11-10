"""Decision-record check: every ADR states its basis and agrees with the index."""

import argparse
import re
from pathlib import Path

from tools._common import DEFAULT_ROOT, Finding, report, tracked_files

INDEX_PATH = "docs/adr/README.md"
RECORD = re.compile(r"^docs/adr/(?P<number>\d{4})-[^/]+\.md$")
FIRST_WITH_BASIS = 8
STATUS = re.compile(r"^\*\*Status:\*\*\s*(?P<status>.+)$", re.MULTILINE)
BASIS = re.compile(r"^## Basis\s*\n(?P<body>.*?)(?=^## |\Z)", re.MULTILINE | re.DOTALL)
INDEX_ROW = re.compile(
    r"^\| \[(?P<number>\d{4})\]\([^)]*\) \|.*\| (?P<status>[^|]+) \|$", re.MULTILINE
)
RECORD_LINK = re.compile(r"\[ADR-(\d{4})\]\([^)]*\)")


def _normalise(status: str) -> str:
    return RECORD_LINK.sub(r"\1", status).strip().lower()


def _status(text: str) -> str:
    match = STATUS.search(text)
    return _normalise(match["status"]) if match else "none"


def _has_basis(text: str) -> bool:
    match = BASIS.search(text)
    return bool(match and match["body"].strip())


def _index_statuses(index: str) -> dict[str, str]:
    return {row["number"]: _normalise(row["status"]) for row in INDEX_ROW.finditer(index)}


def check_records(records: dict[str, str], index: str) -> list[Finding]:
    """`records` maps the path of each English ADR to its text; `index` is the index text."""
    in_index = _index_statuses(index)
    findings: list[Finding] = []
    for path in sorted(records):
        match = RECORD.match(path)
        if match is None:
            continue
        number, text = match["number"], records[path]
        if int(number) >= FIRST_WITH_BASIS and not _has_basis(text):
            findings.append(Finding(path, "no Basis section with text"))
        if number not in in_index:
            findings.append(Finding(path, f"no row in the index {INDEX_PATH}"))
        elif _status(text) != in_index[number]:
            findings.append(
                Finding(
                    path,
                    f"status '{_status(text)}' differs from the index, "
                    f"which says '{in_index[number]}'",
                )
            )
    return findings


def main(argv: list[str] | None = None, root: Path | None = None) -> int:
    argparse.ArgumentParser(description=__doc__).parse_args(argv)
    root = root or DEFAULT_ROOT
    tracked = tracked_files(root)
    records = {
        path: (root / path).read_text(encoding="utf-8")
        for path in tracked
        if RECORD.match(path) and not path.endswith(".es.md")
    }
    index = (root / INDEX_PATH).read_text(encoding="utf-8") if INDEX_PATH in tracked else ""
    return report("adrs", check_records(records, index))


if __name__ == "__main__":
    raise SystemExit(main())
