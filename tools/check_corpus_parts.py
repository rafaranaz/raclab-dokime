"""Parts check: the four parts of the job corpus ended well and ran the whole corpus (ADR-0078).

The job `corpus` gathers the four parts. Each part leaves, in a directory of its own, a file `ran`
that says whether it ran the corpus and, when it did, its JUnit report `corpus.xml`. The check
fails unless every part ended in `success`, and, when the parts ran the corpus, unless they all
did and their reports hold as many tests as one collection of the corpus.
"""

import argparse
import re
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import NoReturn
from xml.parsers import expat

from tools.corpus_parts import PARTS

_COLLECTED = re.compile(r"(\d+) tests? collected")
DID_NOT_RUN = "the corpus did not run: the pull request only changes text"


class _UnreadableError(Exception):
    pass


def _refuse(*_: object) -> NoReturn:
    raise _UnreadableError("the report has a DOCTYPE")


def collected(output: str) -> int:
    """The number of tests in the output of `pytest --collect-only -q`."""
    found = _COLLECTED.findall(output)
    if not found:
        raise ValueError("the output gives no number of tests collected")
    return int(found[-1])


def _tests(report: bytes) -> int:
    count = 0

    def start(tag: str, _: dict[str, str]) -> None:
        nonlocal count
        if tag == "testcase":
            count += 1

    parser = expat.ParserCreate()
    parser.StartDoctypeDeclHandler = _refuse
    parser.EntityDeclHandler = _refuse
    parser.StartElementHandler = start
    try:
        parser.Parse(report, True)
    except expat.ExpatError as error:
        raise _UnreadableError(f"it is not well-formed XML: {error}") from None
    return count


def check_parts(
    results: Mapping[str, str],
    ran: Mapping[str, bool],
    reports: Mapping[str, bytes | None],
    collection: int,
) -> tuple[bool, list[str]]:
    """Say whether the parts ended well and hold the tests of one collection, with its lines."""
    ended = [
        f"part {p}: ended in {results.get(p, 'nothing')}"
        for p in PARTS
        if results.get(p) != "success"
    ]
    if ended:
        return False, ended
    running = [p for p in PARTS if ran.get(p)]
    if not running:
        return True, [DID_NOT_RUN]
    if len(running) < len(PARTS):
        idle = ", ".join(p for p in PARTS if p not in running)
        return False, [f"parts {idle} did not run the corpus while the others did"]
    lines: list[str] = []
    counts: dict[str, int] = {}
    for part in PARTS:
        report = reports.get(part)
        if report is None:
            lines.append(f"part {part}: ran the corpus and left no report")
            continue
        try:
            counts[part] = _tests(report)
        except _UnreadableError as error:
            lines.append(f"part {part}: its report cannot be read: {error}")
    if lines:
        return False, lines
    total = sum(counts.values())
    lines = [f"part {p}: {counts[p]} tests" for p in PARTS]
    if total != collection:
        lines.append(
            f"the parts ran {total} tests, and one collection of the corpus has {collection}"
        )
        return False, lines
    lines.append(f"the parts ran {total} tests, those of one collection of the corpus")
    return True, lines


def _result(text: str) -> tuple[str, str]:
    part, _, ending = text.partition("=")
    return part, ending


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parts", type=Path, required=True, help="the directory of the parts")
    parser.add_argument(
        "--collection", type=Path, required=True, help="the output of one collection"
    )
    parser.add_argument(
        "--result", type=_result, action="append", default=[], help="part=result of each part"
    )
    arguments = parser.parse_args(argv)
    results = dict(arguments.result)
    ran: dict[str, bool] = {}
    reports: dict[str, bytes | None] = {}
    for part in PARTS:
        left = arguments.parts / part
        ran[part] = (left / "ran").is_file() and (left / "ran").read_text().strip() == "true"
        report = left / "corpus.xml"
        reports[part] = report.read_bytes() if report.is_file() else None
    try:
        collection = collected(arguments.collection.read_text())
    except (OSError, ValueError) as error:
        print(f"[corpus] {arguments.collection}: cannot be read: {error}")
        return 1
    passed, lines = check_parts(results, ran, reports, collection)
    for line in lines:
        print(f"[corpus] {line}")
    print("[corpus] OK" if passed else "[corpus] failed")
    sys.stdout.flush()
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
