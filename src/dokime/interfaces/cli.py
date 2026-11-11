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

EXIT_CODES = {Verdict.PASS: 0, Verdict.FAIL: 1, Verdict.ERROR: 2, Verdict.ASK: 3}
_COUNTED = (Verdict.FAIL, Verdict.ASK, Verdict.ERROR)


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command the arguments name and return its exit code."""
    arguments = _parser().parse_args(argv)
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
    lines = [_line(path, finding) for finding in checked.findings]
    return "\n".join([*lines, _summary(checked)]) + "\n"


def _line(path: str, finding: Finding) -> str:
    place = f"{path}:{finding.lines[0]}" if finding.lines else path
    others = finding.lines[1:]
    also = ""
    if others:
        word = "lines" if len(others) > 1 else "line"
        also = f" (also {word} {', '.join(str(line) for line in others)})"
    return f"{place}: {finding.verdict.value} {finding.code}: {finding.message}{also}"


def _summary(checked: Checked) -> str:
    total = len(checked.findings)
    if not total:
        return f"{checked.verdict.value}: no findings"
    counts = [
        f"{count} {verdict.value.lower()}"
        for verdict in _COUNTED
        if (count := sum(finding.verdict is verdict for finding in checked.findings))
    ]
    noun = "finding" if total == 1 else "findings"
    return f"{checked.verdict.value}: {total} {noun} ({', '.join(counts)})"


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
