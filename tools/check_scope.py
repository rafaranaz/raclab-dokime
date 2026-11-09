"""Branch scope check: a branch declares one scope and may only change that scope's paths."""

import argparse
import re
from pathlib import Path

from tools._common import DEFAULT_ROOT, Config, Finding, git, load_config, path_matches, report

BRANCH = re.compile(
    r"^(?P<type>[a-z]+)/(?P<scope>[a-z0-9]+)-(?P<description>[a-z0-9]+(?:-[a-z0-9]+)*)$"
)


def parse_branch(name: str, config: Config) -> tuple[str, str]:
    """Return (type, scope) of a `type/scope-description` branch name, or raise ValueError."""
    match = BRANCH.match(name)
    if match is None or match["type"] not in config.types or match["scope"] not in config.scopes:
        raise ValueError(
            f"branch {name!r} does not match 'type/scope-description' with type in "
            f"{sorted(config.types)} and scope in {sorted(config.scopes)}"
        )
    return match["type"], match["scope"]


def check_changes(files: list[str], scope: str, config: Config) -> list[Finding]:
    allowed = config.scopes[scope] + config.shared
    outside = sorted(f for f in files if not path_matches(f, allowed))
    if not outside:
        return []
    listed = "\n  ".join(outside)
    return [Finding(path=scope, message=f"files outside the scope {scope!r}:\n  {listed}")]


def main(argv: list[str] | None = None, root: Path | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True, help="ref the branch starts from")
    parser.add_argument("--branch", required=True, help="branch name")
    args = parser.parse_args(argv)
    root = root or DEFAULT_ROOT
    config = load_config(root)
    try:
        _, scope = parse_branch(args.branch, config)
    except ValueError as error:
        return report("scope", [Finding(path=args.branch, message=str(error))])
    changed = git(root, "diff", "--name-only", "--no-renames", f"{args.base}...HEAD").splitlines()
    return report("scope", check_changes(changed, scope, config))


if __name__ == "__main__":
    raise SystemExit(main())
