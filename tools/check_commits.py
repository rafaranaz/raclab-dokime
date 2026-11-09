"""Commit message check: Conventional Commits with a closed list of scopes."""

import argparse
import re
from dataclasses import dataclass
from pathlib import Path

from tools._common import DEFAULT_ROOT, Config, Finding, git, load_config, report
from tools.check_scope import parse_branch

MAX_HEADER_LENGTH = 72
HEADER = re.compile(
    r"^(?P<type>[a-z]+)\((?P<scope>[a-z0-9-]+)\)(?P<breaking>!)?: (?P<description>\S.*)$"
)
TRAILER = re.compile(r"^[A-Za-z][A-Za-z-]*: .+$")


@dataclass(frozen=True)
class Commit:
    sha: str
    parents: tuple[str, ...]
    message: str


def _body_without_trailers(message: str) -> str:
    paragraphs = [p.strip() for p in message.strip().split("\n\n")[1:] if p.strip()]
    if paragraphs and all(TRAILER.match(line) for line in paragraphs[-1].splitlines()):
        paragraphs = paragraphs[:-1]
    return "\n\n".join(paragraphs)


def check_commit(commit: Commit, config: Config, branch_scope: str | None) -> list[str]:
    """Return the reasons `commit` is not acceptable; empty when it is."""
    errors: list[str] = []
    header = commit.message.strip().splitlines()[0] if commit.message.strip() else ""
    if len(commit.parents) > 1:
        errors.append("merge commits are not allowed; rebase the branch instead")
    if len(header) > MAX_HEADER_LENGTH:
        errors.append(f"header is {len(header)} characters long, the limit is {MAX_HEADER_LENGTH}")

    match = HEADER.match(header)
    if match is None or match["type"] not in config.types:
        errors.append(
            f"header {header!r} does not match 'type(scope): description' "
            f"with type in {sorted(config.types)}"
        )
        return errors

    scope = match["scope"]
    if scope not in config.scopes:
        errors.append(f"scope {scope!r} is not declared in tools/scopes.toml")
    elif branch_scope is not None and scope != branch_scope:
        errors.append(f"scope {scope!r} differs from the branch scope {branch_scope!r}")
    if match["type"] in config.body_required and not _body_without_trailers(commit.message):
        errors.append(f"commits of type {match['type']!r} need a body explaining why")
    return errors


def read_commits(root: Path, base: str) -> list[Commit]:
    """Commits reachable from HEAD and not from `base`, oldest first."""
    output = git(root, "log", "--reverse", "--format=%H%x00%P%x00%B%x1e", f"{base}..HEAD")
    commits = []
    for record in output.split("\x1e"):
        if not record.strip():
            continue
        sha, parents, message = record.strip("\n").split("\x00", 2)
        commits.append(Commit(sha=sha, parents=tuple(parents.split()), message=message))
    return commits


def main(argv: list[str] | None = None, root: Path | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True, help="ref the branch starts from")
    parser.add_argument("--branch", help="branch name; when given, commit scopes must match it")
    args = parser.parse_args(argv)
    root = root or DEFAULT_ROOT
    config = load_config(root)

    branch_scope = None
    if args.branch:
        try:
            branch_scope = parse_branch(args.branch, config)[1]
        except ValueError as error:
            return report("commits", [Finding(path=args.branch, message=str(error))])

    findings = [
        Finding(path=commit.sha[:10], message=error)
        for commit in read_commits(root, args.base)
        for error in check_commit(commit, config, branch_scope)
    ]
    return report("commits", findings)


if __name__ == "__main__":
    raise SystemExit(main())
