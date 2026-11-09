"""Mermaid check: every Mermaid block in the Markdown files renders.

The rendering is delegated to the Mermaid CLI (`mmdc`), pinned in package.json. When the renderer
cannot be run the check fails instead of skipping the diagrams: an unvalidated diagram must not
pass as a valid one.
"""

import argparse
import re
import shlex
import subprocess
import tempfile
from pathlib import Path

from tools._common import DEFAULT_ROOT, Finding, report, tracked_files

DEFAULT_RENDERER = "node_modules/.bin/mmdc --puppeteerConfigFile tools/mermaid/puppeteer.json"
MERMAID_FENCE = re.compile(r"^\s*(```|~~~)\s*mermaid\s*$", re.MULTILINE)
RENDER_TIMEOUT_SECONDS = 180
# The renderer prints the parse error first and a JavaScript stack trace after it.
ERROR_LINES_SHOWN = 4


def has_mermaid(text: str) -> bool:
    return MERMAID_FENCE.search(text) is not None


def _render(root: Path, path: str, renderer: list[str], output_dir: str) -> str | None:
    """Error message when `path` does not render; None when it does."""
    command = [*renderer, "--quiet", "-i", str(root / path), "-o", f"{output_dir}/out.md"]
    try:
        result = subprocess.run(
            command, cwd=root, capture_output=True, text=True, timeout=RENDER_TIMEOUT_SECONDS
        )
    except FileNotFoundError:
        return f"cannot run the Mermaid renderer {renderer[0]!r}; install it with 'npm ci'"
    except subprocess.TimeoutExpired:
        return f"the Mermaid renderer took longer than {RENDER_TIMEOUT_SECONDS} s"
    if result.returncode != 0:
        lines = (result.stderr or result.stdout).strip().splitlines()
        return "diagram does not render: " + "\n".join(lines[:ERROR_LINES_SHOWN])
    return None


def check_files(root: Path, paths: list[str], renderer: list[str]) -> list[Finding]:
    findings: list[Finding] = []
    with tempfile.TemporaryDirectory() as output_dir:
        for path in paths:
            if not has_mermaid((root / path).read_text(encoding="utf-8")):
                continue
            error = _render(root, path, renderer, output_dir)
            if error is not None:
                findings.append(Finding(path, error))
    return findings


def main(argv: list[str] | None = None, root: Path | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--renderer", default=DEFAULT_RENDERER, help="renderer command line")
    args = parser.parse_args(argv)
    root = root or DEFAULT_ROOT
    paths = sorted(path for path in tracked_files(root) if path.endswith(".md"))
    return report("mermaid", check_files(root, paths, shlex.split(args.renderer)))


if __name__ == "__main__":
    raise SystemExit(main())
