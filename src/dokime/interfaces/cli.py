"""The command line of the harness.

Findings go to the standard output, one per line, and the exit code is that of the verdict.
"""

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from dokime.contract.check import check
from dokime.contract.model import Checked
from dokime.core.findings import Finding
from dokime.core.verdicts import Verdict
from dokime.interfaces.audit_command import audit_command
from dokime.interfaces.env import env_check
from dokime.interfaces.text import EXIT_CODES, finding_line, summary


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command the arguments name and return its exit code."""
    arguments = _parser().parse_args(argv)
    if arguments.area == "env":
        return env_check(arguments)
    if arguments.area == "audit":
        return audit_command(arguments)
    checked = _check_file(arguments.path)
    write = _as_json if arguments.format == "json" else _as_text
    sys.stdout.write(write(str(arguments.path), checked))
    return EXIT_CODES[checked.verdict]


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="dokime", description="Verification and evidence around coding agents."
    )
    areas = parser.add_subparsers(dest="area", required=True, metavar="AREA")
    contract = areas.add_parser("contract", help="work with a contract")
    actions = contract.add_subparsers(dest="action", required=True, metavar="ACTION")
    check_one = actions.add_parser(
        "check", help="validate a contract file and say what it lacks", description=__doc__
    )
    check_one.add_argument("path", type=Path, help="the contract file")
    check_one.add_argument(
        "--format", choices=("text", "json"), default="text", help="how the findings are written"
    )
    env = areas.add_parser("env", help="work with the environment of a verified project")
    env_actions = env.add_subparsers(dest="action", required=True, metavar="ACTION")
    env_one = env_actions.add_parser(
        "check",
        help="self-check a pack on the history of its project",
        description="Self-check a pack: find two commits whose tests go from red to green.",
    )
    env_one.add_argument(
        "--from", dest="start", required=True, help="the full name of the commit to start from"
    )
    env_one.add_argument(
        "--project", type=Path, default=Path(), help="the project; the current directory if absent"
    )
    env_one.add_argument(
        "--pack",
        type=Path,
        default=None,
        help="the pack; .dokime/pack.yaml of the project if absent",
    )
    env_one.add_argument(
        "--format", choices=("text", "json"), default="text", help="how the result is written"
    )
    audit = areas.add_parser(
        "audit",
        help="audit a change that arrives already made",
        description="Audit a patch on a base commit against its contract, and write its evidence.",
    )
    audit.add_argument(
        "--project", type=Path, default=Path(), help="the project; the current directory if absent"
    )
    audit.add_argument("--base", required=True, help="the full name of the base commit")
    audit.add_argument("--patch", type=Path, required=True, help="the file of the patch")
    audit.add_argument("--story", default=None, help="the story of the change in the base")
    audit.add_argument(
        "--contract", type=Path, default=None, help="the contract, from outside the patch"
    )
    audit.add_argument("--pack", type=Path, default=None, help="the pack, from outside the patch")
    audit.add_argument(
        "--out", type=Path, required=True, help="an empty directory outside the project"
    )
    audit.add_argument(
        "--format", choices=("text", "json"), default="text", help="how the result is written"
    )
    return parser


def _check_file(path: Path) -> Checked:
    """Check the contract in a file. A file that cannot be read is a finding, not a crash."""
    try:
        text = path.read_bytes().decode("utf-8")
    except OSError as error:
        reason = error.strerror or type(error).__name__
    except UnicodeDecodeError:
        reason = "it is not UTF-8 text"
    else:
        return check(text)
    unreadable = Finding(
        code="unreadable-file", message=f"the file cannot be read: {reason}", verdict=Verdict.ERROR
    )
    return Checked(contract=None, findings=(unreadable,))


def _as_text(path: str, checked: Checked) -> str:
    lines = [finding_line(path, finding) for finding in checked.findings]
    return "\n".join([*lines, summary(checked.verdict, checked.findings)]) + "\n"


def _as_json(path: str, checked: Checked) -> str:
    document = {
        "file": path,
        "verdict": checked.verdict.value,
        "findings": [
            {
                "code": finding.code,
                "verdict": finding.verdict.value,
                "message": finding.message,
                "lines": list(finding.lines),
            }
            for finding in checked.findings
        ],
    }
    return json.dumps(document, indent=2, ensure_ascii=False) + "\n"
