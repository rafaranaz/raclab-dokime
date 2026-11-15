"""Gate runner: run every command of the block "Gates locally" of CLAUDE.md.

Each line of the block runs in a bash of its own with `set -euo pipefail`, so that a failure inside
a pipeline or before the last `&&` of a line ends that line with its exit code. The runner stops at
the first line that fails and ends with that code.
"""

import argparse
import re
import shlex
import subprocess
import sys
from pathlib import Path

from tools._common import DEFAULT_ROOT

BLOCK = re.compile(r"^## Gates locally\n.*?^```bash\n(?P<body>.*?)^```", re.DOTALL | re.MULTILINE)
BRANCH = "<branch>"


def gate_block(text: str) -> str | None:
    """Return the commands of the block "Gates locally", or None when there is none."""
    found = BLOCK.search(text)
    return found["body"] if found else None


def _current_branch(root: Path) -> str:
    done = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "--abbrev-ref", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    )
    return done.stdout.strip()


def main(argv: list[str] | None = None, root: Path | None = None) -> int:
    argparse.ArgumentParser(description=__doc__).parse_args(argv)
    root = root or DEFAULT_ROOT
    block = gate_block((root / "CLAUDE.md").read_text(encoding="utf-8"))
    if block is None:
        print("[gates] CLAUDE.md has no block 'Gates locally'", file=sys.stderr)
        return 1
    branch = _current_branch(root)
    for line in block.replace(BRANCH, shlex.quote(branch)).splitlines():
        if not line.strip():
            continue
        print(f"[gates] {line}", file=sys.stderr, flush=True)
        done = subprocess.run(["bash", "-euo", "pipefail", "-c", line], cwd=root, check=False)
        if done.returncode != 0:
            print(f"[gates] failed with {done.returncode}: {line}", file=sys.stderr)
            return done.returncode
    print("[gates] OK", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
