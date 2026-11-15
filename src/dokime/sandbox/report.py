"""The reader of a test report in JUnit XML, shared by the adapters of the verification runtime.

The report is written by the code under check, so it is read with a bound on its size and with
`pyexpat` handlers that refuse a `DOCTYPE` before any entity is declared (ADR-0045). The reader
runs in the process of the harness, and opens the path without refusing links, until the
hardening of ADR-0045.
"""

import errno
import os
import stat
from pathlib import Path, PurePosixPath
from typing import NoReturn
from xml.parsers import expat

from dokime.core.outcomes import Outcome, Report, ReportLimits
from dokime.core.repository import RefusalError

_CHILDREN = {"failure": Outcome.FAILED, "error": Outcome.ERROR, "skipped": Outcome.SKIPPED}
_PRECEDENCE = (Outcome.ERROR, Outcome.FAILED, Outcome.SKIPPED)


class _DoctypeError(Exception):
    pass


def _refuse_doctype(*_: object) -> NoReturn:
    raise _DoctypeError


class _Cases:
    """Collects the outcome of each test case as the parser goes through the report."""

    def __init__(self) -> None:
        self.report: dict[str, Outcome] = {}
        self._case: str | None = None
        self._seen: set[Outcome] = set()

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
            raise RefusalError(
                "report-duplicate-test", f"the report names the test {self._case!r} twice"
            )
        outcome = next((o for o in _PRECEDENCE if o in self._seen), Outcome.PASSED)
        self.report[self._case] = outcome
        self._case = None


def _not_a_file(report: PurePosixPath, why: str) -> RefusalError:
    return RefusalError("report-not-a-file", f"the report {report} is not a regular file: {why}")


def _open(output: Path, report: PurePosixPath) -> int:
    """Open the report part by part from the output directory, following no link."""
    directory = os.open(output, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
    try:
        *parents, name = report.parts
        for part in parents:
            opened = _open_part(
                part, directory, report, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
            )
            os.close(directory)
            directory = opened
        descriptor = _open_part(
            name, directory, report, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK
        )
    finally:
        os.close(directory)
    if not stat.S_ISREG(os.fstat(descriptor).st_mode):
        os.close(descriptor)
        raise _not_a_file(report, "it is not a file")
    return descriptor


def _open_part(part: str, directory: int, report: PurePosixPath, flags: int) -> int:
    try:
        return os.open(part, flags | os.O_CLOEXEC, dir_fd=directory)
    except FileNotFoundError:
        raise RefusalError("report-missing", f"the run wrote no report at {report}") from None
    except OSError as error:
        if error.errno in (errno.ELOOP, errno.ENOTDIR):
            raise _not_a_file(report, f"{part!r} is a link or not a directory") from None
        raise RefusalError(
            "report-unreadable", f"the report {report} cannot be read: {error}"
        ) from None


def read_report(output: Path, report: PurePosixPath, limits: ReportLimits) -> Report:
    """Read the report at `report` inside the output directory."""
    if report.is_absolute() or ".." in report.parts:
        raise RefusalError(
            "path-outside-output", f"the path of the report {str(report)!r} leaves the output"
        )
    descriptor = _open(output, report)
    try:
        with os.fdopen(descriptor, "rb", closefd=False) as handle:
            data = handle.read(limits.report_bytes + 1)
    except OSError as error:
        raise RefusalError(
            "report-unreadable", f"the report {report} cannot be read: {error}"
        ) from None
    finally:
        os.close(descriptor)
    if len(data) > limits.report_bytes:
        raise RefusalError(
            "report-too-large",
            f"the report {report} is larger than its limit of {limits.report_bytes} bytes",
        )
    cases = _Cases()
    parser = expat.ParserCreate()
    parser.StartDoctypeDeclHandler = _refuse_doctype
    parser.EntityDeclHandler = _refuse_doctype
    parser.ExternalEntityRefHandler = _refuse_doctype
    parser.StartElementHandler = cases.start
    parser.EndElementHandler = cases.end
    try:
        parser.Parse(data, True)
    except _DoctypeError:
        raise RefusalError("report-has-doctype", f"the report {report} has a DOCTYPE") from None
    except expat.ExpatError as error:
        raise RefusalError(
            "report-unreadable", f"the report {report} is not well-formed XML: {error}"
        ) from None
    return cases.report
