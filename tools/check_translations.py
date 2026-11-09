"""Translation check: every documentation file has a Spanish translation that is up to date.

English is the source. The translation lives next to it as `<name>.es.md` and its first line
records the hash of the English text it was translated from:
`<!-- translation-of: <name>.md sha256:<hash> -->`. When the English file changes, the hash no
longer matches and the translation has to be reviewed and stamped again.
"""

import argparse
import hashlib
import posixpath
import re
from pathlib import Path

from tools._common import DEFAULT_ROOT, Finding, path_matches, report, tracked_files

DOCUMENTATION = ("README.md", "CONTRIBUTING.md", "docs/**")
NOT_DOCUMENTATION = ("docs/requirements/**",)
SPANISH_SUFFIX = ".es.md"
HEADER = re.compile(r"^<!-- translation-of: (?P<source>\S+) sha256:(?P<hash>[0-9a-f]+) -->$")


def is_documentation(path: str) -> bool:
    """True for English, human-facing Markdown that must have a Spanish translation."""
    return (
        path.endswith(".md")
        and not path.endswith(SPANISH_SUFFIX)
        and path_matches(path, DOCUMENTATION)
        and not path_matches(path, NOT_DOCUMENTATION)
    )


def source_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def header_for(source_name: str, source_text: str) -> str:
    """The first line a translation of `source_name` must carry."""
    return f"<!-- translation-of: {source_name} sha256:{source_hash(source_text)} -->"


def _translation_of(path: str) -> str:
    return path[: -len(".md")] + SPANISH_SUFFIX


def _source_of(path: str) -> str:
    return path[: -len(SPANISH_SUFFIX)] + ".md"


def _check_translation(path: str, text: str, files: dict[str, str]) -> Finding | None:
    source = _source_of(path)
    if source not in files:
        return Finding(path, f"translation has no English source {posixpath.basename(source)}")
    first_line = text.split("\n", 1)[0].strip()
    match = HEADER.match(first_line)
    expected = header_for(posixpath.basename(source), files[source])
    if match is None or match["source"] != posixpath.basename(source):
        return Finding(path, f"first line must be the source header: {expected}", 1)
    if match["hash"] != source_hash(files[source]):
        return Finding(
            path, f"translation is out of date with its source; review it and set: {expected}", 1
        )
    return None


def check(files: dict[str, str]) -> list[Finding]:
    """`files` maps every tracked Markdown path to its text."""
    findings: list[Finding] = []
    for path, text in sorted(files.items()):
        if is_documentation(path) and _translation_of(path) not in files:
            name = posixpath.basename(_translation_of(path))
            findings.append(Finding(path, f"missing Spanish translation {name}"))
        elif path.endswith(SPANISH_SUFFIX):
            finding = _check_translation(path, text, files)
            if finding is not None:
                findings.append(finding)
    return findings


def main(argv: list[str] | None = None, root: Path | None = None) -> int:
    argparse.ArgumentParser(description=__doc__).parse_args(argv)
    root = root or DEFAULT_ROOT
    files = {
        path: (root / path).read_text(encoding="utf-8")
        for path in tracked_files(root)
        if path.endswith(".md")
    }
    return report("translations", check(files))


if __name__ == "__main__":
    raise SystemExit(main())
