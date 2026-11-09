"""Link check: relative links in Markdown files point to tracked files or directories."""

import argparse
import posixpath
import re
from pathlib import Path

from tools._common import DEFAULT_ROOT, Finding, report, tracked_files

LINK = re.compile(r"!?\[[^\]]*\]\((?P<target>[^)\s]+)(?:\s+\"[^\"]*\")?\)")
FENCE = re.compile(r"^(```|~~~)")
INLINE_CODE = re.compile(r"`[^`]*`")
EXTERNAL = ("http://", "https://", "mailto:", "#")


def _exists(target: str, tracked: frozenset[str]) -> bool:
    if target in tracked:
        return True
    directory = target.rstrip("/") + "/"
    return any(path.startswith(directory) for path in tracked)


def check_markdown(path: str, text: str, tracked: frozenset[str]) -> list[Finding]:
    findings: list[Finding] = []
    in_fence = False
    for number, line in enumerate(text.splitlines(), start=1):
        if FENCE.match(line.strip()):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        for match in LINK.finditer(INLINE_CODE.sub("", line)):
            target = match["target"]
            if target.startswith(EXTERNAL):
                continue
            relative = target.split("#", 1)[0].split("?", 1)[0]
            base = "" if relative.startswith("/") else posixpath.dirname(path)
            resolved = posixpath.normpath(posixpath.join(base, relative.lstrip("/")))
            if not _exists(resolved, tracked):
                findings.append(Finding(path, f"broken link: {target}", number))
    return findings


def main(argv: list[str] | None = None, root: Path | None = None) -> int:
    argparse.ArgumentParser(description=__doc__).parse_args(argv)
    root = root or DEFAULT_ROOT
    tracked = frozenset(tracked_files(root))
    findings: list[Finding] = []
    for path in sorted(tracked):
        if path.endswith(".md"):
            findings.extend(
                check_markdown(path, (root / path).read_text(encoding="utf-8"), tracked)
            )
    return report("links", findings)


if __name__ == "__main__":
    raise SystemExit(main())
