"""History check: comments and docstrings describe what the code does, not how it got there.

History belongs to git and to the ADRs. This check rejects the markers that only make sense as
history (task identifiers, version tags, dates, narrative phrases) and references to Markdown
files that do not exist.
"""

import argparse
import io
import posixpath
import re
import tokenize
from pathlib import Path

from tools._common import DEFAULT_ROOT, Finding, report, tracked_files

SCANNED_FOLDERS = ("src/", "tests/", "tools/")

HISTORY_MARKERS = (
    ("task identifier", re.compile(r"\bT\d+b?\.\d+\b|\bDT-\d+\b")),
    ("version tag", re.compile(r"\bv\d+\.\d+(?:\.\d+)?\b")),
    ("date", re.compile(r"\b\d{4}-\d{2}-\d{2}\b")),
    (
        "history phrase",
        re.compile(r"\b(used to|root cause|was changed|before this change|after the fix)\b", re.I),
    ),
)
MARKDOWN_REFERENCE = re.compile(r"(?<![\w/.-])([\w./-]+\.md)\b")

_DOCSTRING_PREDECESSORS = {
    tokenize.INDENT,
    tokenize.DEDENT,
    tokenize.NEWLINE,
    tokenize.NL,
    tokenize.ENCODING,
}


def _prose_lines(source: str) -> list[tuple[int, str]]:
    """(line number, text) for every comment and docstring line in `source`."""
    lines: list[tuple[int, str]] = []
    previous: int | None = None
    depth = 0
    for token in tokenize.generate_tokens(io.StringIO(source).readline):
        if token.type == tokenize.OP and token.string in "([{":
            depth += 1
        elif token.type == tokenize.OP and token.string in ")]}":
            depth -= 1
        is_docstring = (
            token.type == tokenize.STRING
            and depth == 0
            and (previous is None or previous in _DOCSTRING_PREDECESSORS)
        )
        if token.type == tokenize.COMMENT or is_docstring:
            for offset, text in enumerate(token.string.splitlines()):
                lines.append((token.start[0] + offset, text))
        if token.type != tokenize.COMMENT:
            previous = token.type
    return lines


def _missing_reference(reference: str, path: str, markdown_files: frozenset[str]) -> bool:
    candidates = {
        posixpath.normpath(reference),
        posixpath.normpath(posixpath.join(posixpath.dirname(path), reference)),
    }
    return candidates.isdisjoint(markdown_files)


def scan_source(source: str, path: str, markdown_files: frozenset[str]) -> list[Finding]:
    try:
        lines = _prose_lines(source)
    except (tokenize.TokenError, SyntaxError) as error:
        return [Finding(path=path, message=f"cannot tokenize the file: {error}")]

    findings: list[Finding] = []
    for number, text in lines:
        for label, pattern in HISTORY_MARKERS:
            for match in pattern.finditer(text):
                findings.append(Finding(path, f"{label} in prose: {match.group(0)!r}", number))
        for match in MARKDOWN_REFERENCE.finditer(text):
            if _missing_reference(match.group(1), path, markdown_files):
                findings.append(
                    Finding(path, f"reference to a missing file: {match.group(1)}", number)
                )
    return findings


def main(argv: list[str] | None = None, root: Path | None = None) -> int:
    argparse.ArgumentParser(description=__doc__).parse_args(argv)
    root = root or DEFAULT_ROOT
    files = tracked_files(root)
    markdown_files = frozenset(f for f in files if f.endswith(".md"))
    findings: list[Finding] = []
    for path in files:
        if path.endswith(".py") and path.startswith(SCANNED_FOLDERS):
            source = (root / path).read_text(encoding="utf-8")
            findings.extend(scan_source(source, path, markdown_files))
    return report("history", findings)


if __name__ == "__main__":
    raise SystemExit(main())
