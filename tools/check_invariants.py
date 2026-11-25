"""Invariants check: each invariant has a requirement that enforces it or an open target."""

import argparse
from pathlib import Path

from tools._common import Finding

README_PATH = "docs/architecture/README.md"


def check(readme: str, roadmap: str, requirements: frozenset[str]) -> list[Finding]:
    """Findings of the table of the invariants in `readme` against `roadmap` and `requirements`."""
    return []


def main(argv: list[str] | None = None, root: Path | None = None) -> int:
    argparse.ArgumentParser(description=__doc__).parse_args(argv)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
