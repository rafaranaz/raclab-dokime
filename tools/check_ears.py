"""EARS check: every requirement follows one EARS template, states one behaviour and is measurable.

Requirements live in docs/requirements/<scope>.md, one per line:
`- **<PREFIX>-<NNN>** <statement>`, where PREFIX is the file name in upper case.
"""

import argparse
import re
from pathlib import Path

from tools._common import DEFAULT_ROOT, Finding, report

REQUIREMENTS_DIR = Path("docs/requirements")

REQUIREMENT_LINE = re.compile(r"^- \*\*(?P<id>[^*]+)\*\*\s+(?P<statement>.+)$")
IDENTIFIER = re.compile(r"^[A-Z]+-\d{3}$")
CODE_SPAN = re.compile(r"`[^`]*`")
SHALL = re.compile(r"\bshall\b")

_SUBJECT = r"the [^,]+? shall \S.*\."
TEMPLATES = (
    ("ubiquitous", re.compile(r"^The [^,]+? shall \S.*\.$")),
    ("event-driven", re.compile(rf"^When .+?, {_SUBJECT}$")),
    ("state-driven", re.compile(rf"^While .+?, (?:when .+?, )?{_SUBJECT}$")),
    ("unwanted behaviour", re.compile(rf"^If .+?, then {_SUBJECT}$")),
    ("optional feature", re.compile(rf"^Where .+?, {_SUBJECT}$")),
)

VAGUE_TERMS = (
    "adequate",
    "adequately",
    "and/or",
    "appropriate",
    "appropriately",
    "as needed",
    "correctly",
    "easily",
    "easy",
    "efficient",
    "efficiently",
    "etc",
    "fast",
    "flexible",
    "if possible",
    "normally",
    "properly",
    "quickly",
    "reasonable",
    "robust",
    "sufficient",
    "user-friendly",
    "usually",
)
VAGUE = re.compile(
    r"(?<![\w-])(" + "|".join(re.escape(t) for t in VAGUE_TERMS) + r")(?![\w-])", re.I
)


def check_statement(statement: str) -> list[str]:
    """Return the reasons `statement` is not an acceptable EARS requirement."""
    errors: list[str] = []
    if not any(pattern.match(statement) for _, pattern in TEMPLATES):
        names = ", ".join(name for name, _ in TEMPLATES)
        errors.append(f"does not match any EARS template ({names})")
    prose = CODE_SPAN.sub("", statement)
    for match in VAGUE.finditer(prose):
        errors.append(f"vague term {match.group(1)!r}: state a measurable condition instead")
    shall_count = len(SHALL.findall(prose))
    if shall_count > 1:
        errors.append(f"contains 'shall' {shall_count} times: split it into one requirement each")
    return errors


def parse_requirements(text: str) -> list[tuple[str, str, int]]:
    """(identifier, statement, line number) for every requirement line in `text`."""
    requirements = []
    for number, line in enumerate(text.splitlines(), start=1):
        match = REQUIREMENT_LINE.match(line)
        if match:
            requirements.append((match["id"], match["statement"].strip(), number))
    return requirements


def check_file(path: str, text: str) -> list[Finding]:
    prefix = Path(path).stem.upper() + "-"
    findings: list[Finding] = []
    seen: set[str] = set()
    for identifier, statement, number in parse_requirements(text):
        if not IDENTIFIER.match(identifier):
            findings.append(Finding(path, f"malformed identifier {identifier!r}", number))
        elif not identifier.startswith(prefix):
            findings.append(Finding(path, f"{identifier} must start with {prefix}", number))
        if identifier in seen:
            findings.append(Finding(path, f"{identifier} is duplicated", number))
        seen.add(identifier)
        findings.extend(
            Finding(path, f"{identifier} {e}", number) for e in check_statement(statement)
        )
    return findings


def main(argv: list[str] | None = None, root: Path | None = None) -> int:
    argparse.ArgumentParser(description=__doc__).parse_args(argv)
    root = root or DEFAULT_ROOT
    findings: list[Finding] = []
    for file in sorted((root / REQUIREMENTS_DIR).glob("*.md")):
        relative = file.relative_to(root).as_posix()
        findings.extend(check_file(relative, file.read_text(encoding="utf-8")))
    return report("ears", findings)


if __name__ == "__main__":
    raise SystemExit(main())
