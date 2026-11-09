"""Shared helpers for the governance checks: configuration, git access and reporting."""

import fnmatch
import subprocess
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path

DEFAULT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = Path("tools/scopes.toml")


@dataclass(frozen=True)
class Finding:
    """A single problem found by a check, located as precisely as the check can."""

    path: str
    message: str
    line: int | None = None

    def __str__(self) -> str:
        location = f"{self.path}:{self.line}" if self.line is not None else self.path
        return f"{location}: {self.message}"


@dataclass(frozen=True)
class Config:
    """The closed lists from tools/scopes.toml."""

    types: frozenset[str]
    body_required: frozenset[str]
    shared: tuple[str, ...]
    scopes: dict[str, tuple[str, ...]]


def load_config(root: Path) -> Config:
    data = tomllib.loads((root / CONFIG_PATH).read_text(encoding="utf-8"))
    return Config(
        types=frozenset(data["types"]),
        body_required=frozenset(data["body_required"]),
        shared=tuple(data["shared"]),
        scopes={name: tuple(spec["paths"]) for name, spec in data["scopes"].items()},
    )


def path_matches(path: str, patterns: tuple[str, ...]) -> bool:
    """True when `path` equals a pattern, falls under a `dir/**` pattern or matches a glob."""
    for pattern in patterns:
        if pattern.endswith("/**"):
            if path.startswith(pattern[:-2]):
                return True
        elif path == pattern or fnmatch.fnmatchcase(path, pattern):
            return True
    return False


def git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, text=True, check=True
    )
    return result.stdout


def tracked_files(root: Path) -> list[str]:
    """Paths tracked by git, relative to the repository root."""
    return [line for line in git(root, "ls-files", "-z").split("\0") if line]


def report(check_name: str, findings: list[Finding]) -> int:
    """Print the findings and return the process exit code."""
    for finding in findings:
        print(f"[{check_name}] {finding}", file=sys.stderr)
    if findings:
        print(f"[{check_name}] {len(findings)} problem(s) found", file=sys.stderr)
        return 1
    print(f"[{check_name}] OK")
    return 0
