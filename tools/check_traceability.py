"""Traceability check: every requirement has a test, and every test declares what it proves.

A test file declares the requirements it covers on its first non-empty line:
`# SDD-EARS: <ID> <ID> ...`.
"""

import argparse
import re
from pathlib import Path

from tools._common import DEFAULT_ROOT, Finding, report, tracked_files
from tools.check_ears import REQUIREMENTS_DIR, parse_requirements

MARKER = re.compile(r"^#\s*SDD-EARS:\s*(?P<ids>.+)$")


def read_marker(source: str) -> list[str] | None:
    """Requirement identifiers declared by the file, or None when it has no marker."""
    first = next((line.strip() for line in source.splitlines() if line.strip()), "")
    match = MARKER.match(first)
    if match is None:
        return None
    return [identifier for identifier in re.split(r"[\s,]+", match["ids"]) if identifier]


def check(requirements: dict[str, str], tests: dict[str, str]) -> list[Finding]:
    """`requirements` maps identifier to its file; `tests` maps test path to its source."""
    findings: list[Finding] = []
    covered: set[str] = set()
    for path, source in sorted(tests.items()):
        declared = read_marker(source)
        if declared is None:
            findings.append(Finding(path, "first non-empty line must be '# SDD-EARS: <ids>'", 1))
            continue
        unknown = [identifier for identifier in declared if identifier not in requirements]
        if unknown:
            findings.append(Finding(path, f"marker declares unknown requirements: {unknown}", 1))
        covered.update(declared)
    for identifier, file in sorted(requirements.items()):
        if identifier not in covered:
            findings.append(Finding(file, f"{identifier} is not covered by any test"))
    return findings


def main(argv: list[str] | None = None, root: Path | None = None) -> int:
    argparse.ArgumentParser(description=__doc__).parse_args(argv)
    root = root or DEFAULT_ROOT
    requirements: dict[str, str] = {}
    for file in sorted((root / REQUIREMENTS_DIR).glob("*.md")):
        relative = file.relative_to(root).as_posix()
        for identifier, _, _ in parse_requirements(file.read_text(encoding="utf-8")):
            requirements[identifier] = relative
    tests = {
        path: (root / path).read_text(encoding="utf-8")
        for path in tracked_files(root)
        if path.startswith("tests/")
        and Path(path).name.startswith("test_")
        and path.endswith(".py")
    }
    return report("traceability", check(requirements, tests))


if __name__ == "__main__":
    raise SystemExit(main())
