"""The program that parses a test report in JUnit XML, in a process of its own.

The adapter starts it with `python -I` and reads one JSON object on its output: `{"cases": {name:
outcome}}`, or `{"refusal": code, "detail": text}`. It imports only the standard library, so that
it needs nothing of the harness. The report is refused if it is larger than its limit, has a
`DOCTYPE`, is not well-formed or names a test twice (ADR-0045).
"""

import json
import sys
from typing import NoReturn
from xml.parsers import expat

_CHILDREN = {"failure": "failed", "error": "error", "skipped": "skipped"}
_PRECEDENCE = ("error", "failed", "skipped")


class _RefusedError(Exception):
    def __init__(self, code: str, detail: str = "") -> None:
        super().__init__(code)
        self.code = code
        self.detail = detail


def _refuse_doctype(*_: object) -> NoReturn:
    raise _RefusedError("report-has-doctype")


class _Cases:
    """Collects the outcome of each test case as the parser goes through the report."""

    def __init__(self) -> None:
        self.report: dict[str, str] = {}
        self._case: str | None = None
        self._seen: set[str] = set()

    def start(self, tag: str, attributes: dict[str, str]) -> None:
        if tag == "testcase" and self._case is None:
            self._case = f"{attributes.get('classname', '')}::{attributes.get('name', '')}"
            self._seen = set()
        elif self._case is not None and tag in _CHILDREN:
            self._seen.add(_CHILDREN[tag])

    def end(self, tag: str) -> None:
        if tag != "testcase" or self._case is None:
            return
        if self._case in self.report:
            raise _RefusedError("report-duplicate-test", self._case)
        self.report[self._case] = next((o for o in _PRECEDENCE if o in self._seen), "passed")
        self._case = None


def read(source: str, limit: int) -> dict[str, object]:
    """Parse the report and give its cases, or the refusal and its detail."""
    with open(source, "rb") as handle:
        data = handle.read(limit + 1)
    if len(data) > limit:
        return {"refusal": "report-too-large", "detail": ""}
    cases = _Cases()
    parser = expat.ParserCreate()
    parser.StartDoctypeDeclHandler = _refuse_doctype
    parser.EntityDeclHandler = _refuse_doctype
    parser.ExternalEntityRefHandler = _refuse_doctype
    parser.StartElementHandler = cases.start
    parser.EndElementHandler = cases.end
    try:
        parser.Parse(data, True)
    except _RefusedError as refused:
        return {"refusal": refused.code, "detail": refused.detail}
    except expat.ExpatError as error:
        return {"refusal": "report-unreadable", "detail": str(error)}
    return {"cases": cases.report}


def main(argv: list[str]) -> None:
    """Read the report named by the arguments: its source and its limit of size in bytes."""
    source, limit = argv[1], int(argv[2])
    sys.stdout.write(json.dumps(read(source, limit)))


if __name__ == "__main__":
    main(sys.argv)
