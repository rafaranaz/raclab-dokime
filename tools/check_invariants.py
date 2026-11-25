"""Invariants check: each invariant has a requirement that enforces it or an open target.

The table under `## Invariants` of the architecture index names, for each invariant, the
requirements that enforce it today and, in `Not yet`, what is not built with the block or the
milestone of the roadmap that brings it. A target is closed when the roadmap says so in bold.
"""

import argparse
import re
from collections import Counter
from pathlib import Path

from tools._common import DEFAULT_ROOT, Finding, report, tracked_files
from tools.check_ears import parse_requirements

README_PATH = "docs/architecture/README.md"
ROADMAP_PATH = "docs/ROADMAP.md"
REQUIREMENTS_DIR = "docs/requirements/"
HEADING = "## Invariants"
COLUMNS = ("Id", "Invariant", "Enforced today by", "Not yet")
NONE = "—"
REQUIREMENT = re.compile(r"\b(?!ADR-|INV-)([A-Z]+-\d+)\b")
BLOCK_TARGET = re.compile(r"\bblock ([A-Z])\b")
MILESTONE_TARGET = re.compile(r"\b([A-Z]\d+[a-z]?)\b")
BLOCK_ROW = re.compile(r"^\| ([A-Z]) · ", re.MULTILINE)
MILESTONE_ROW = re.compile(r"^\| ([A-Z]\d+[a-z]?) ", re.MULTILINE)
BOLD = re.compile(r"\*\*([^*\n]+)\*\*")


def _cells(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def _table(readme: str) -> list[tuple[int, list[str]]] | None:
    """(line number, cells) of each row of the first table under the heading, or None."""
    lines = readme.splitlines()
    try:
        start = lines.index(HEADING)
    except ValueError:
        return None
    rows: list[tuple[int, list[str]]] = []
    for number, line in enumerate(lines[start + 1 :], start=start + 2):
        if line.startswith("## "):
            break
        if line.startswith("|"):
            rows.append((number, _cells(line)))
        elif rows:
            break
    if len(rows) < 2 or tuple(rows[0][1]) != COLUMNS:
        return None
    return rows[2:]


def _closed(roadmap: str) -> tuple[set[str], set[str]]:
    """The milestones and the blocks that the roadmap marks as closed in bold."""
    milestones: set[str] = set()
    blocks: set[str] = set()
    for text in BOLD.findall(roadmap):
        milestone = re.match(r"([A-Z]\d+[a-z]?) (closed on|is done)", text)
        if milestone:
            milestones.add(milestone[1])
        block = re.match(r"Block ([A-Z]) closed on", text) or re.search(
            r"and block ([A-Z]) with it$", text
        )
        if block:
            blocks.add(block[1])
    return milestones, blocks


def _targets(not_yet: str) -> list[tuple[str, str]]:
    """(kind, name) of each target of a cell, blocks first, in the order of the text."""
    blocks = [("block", name) for name in BLOCK_TARGET.findall(not_yet)]
    milestones = [("milestone", name) for name in MILESTONE_TARGET.findall(not_yet)]
    return blocks + milestones


class _Roadmap:
    """The blocks and the milestones that the roadmap holds, and those it marks as closed."""

    def __init__(self, roadmap: str) -> None:
        self.known = {
            "block": set(BLOCK_ROW.findall(roadmap)),
            "milestone": set(MILESTONE_ROW.findall(roadmap)),
        }
        milestones, blocks = _closed(roadmap)
        self.closed = {"block": blocks, "milestone": milestones}


def _row(cells: list[str], roadmap: _Roadmap, requirements: frozenset[str]) -> list[str]:
    """The messages of one row of the table."""
    name, enforced, not_yet = cells[0], cells[2], cells[3]
    named = REQUIREMENT.findall(enforced)
    messages: list[str] = []
    if not named and not_yet == NONE:
        messages.append(f"{name}: names no requirement and its 'Not yet' is '{NONE}'")
    for requirement in named:
        if requirement not in requirements:
            where = f"no file of {REQUIREMENTS_DIR} defines"
            messages.append(f"{name}: names {requirement}, which {where}")
    if not_yet == NONE:
        return messages
    targets = _targets(not_yet)
    if not targets:
        messages.append(f"{name}: 'Not yet' names no block and no milestone")
    for kind, target in targets:
        label = f"block {target}" if kind == "block" else target
        if target not in roadmap.known[kind]:
            messages.append(f"{name}: names {label}, which {ROADMAP_PATH} does not hold")
        elif target in roadmap.closed[kind]:
            messages.append(f"{name}: points to {label}, which is closed")
    return messages


def check(readme: str, roadmap: str, requirements: frozenset[str]) -> list[Finding]:
    """Findings of the table of the invariants in `readme` against `roadmap` and `requirements`."""
    rows = _table(readme)
    if rows is None:
        expected = " | ".join(COLUMNS)
        return [Finding(README_PATH, f"no table under '{HEADING}' with the columns {expected}")]
    counts = Counter(cells[0] for _, cells in rows)
    findings = [
        Finding(README_PATH, f"{name}: appears in {count} rows")
        for name, count in counts.items()
        if count > 1
    ]
    known = _Roadmap(roadmap)
    for number, cells in rows:
        findings.extend(
            Finding(README_PATH, message, number) for message in _row(cells, known, requirements)
        )
    return findings


def main(argv: list[str] | None = None, root: Path | None = None) -> int:
    argparse.ArgumentParser(description=__doc__).parse_args(argv)
    root = root or DEFAULT_ROOT
    tracked = tracked_files(root)
    requirements = frozenset(
        identifier
        for path in tracked
        if path.startswith(REQUIREMENTS_DIR) and path.endswith(".md")
        for identifier, _, _ in parse_requirements((root / path).read_text(encoding="utf-8"))
    )
    readme = (root / README_PATH).read_text(encoding="utf-8") if README_PATH in tracked else ""
    roadmap = (root / ROADMAP_PATH).read_text(encoding="utf-8") if ROADMAP_PATH in tracked else ""
    return report("invariants", check(readme, roadmap, requirements))


if __name__ == "__main__":
    raise SystemExit(main())
