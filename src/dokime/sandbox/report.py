"""The reader of a test report in JUnit XML, shared by the adapters of the verification runtime.

The report is written by the code under check (ADR-0045). The adapter opens it part by part from
the output directory following no link, and passes the open file to a program of its own, which
sets its limits of memory and processor time before it reads, bounds the size, and refuses a
`DOCTYPE` with handlers of `pyexpat` before any entity is declared. That process bounds the parser
and turns its crash into a refusal; it is not isolation, since it runs with the permissions of the
person.
"""

import errno
import json
import os
import pyexpat
import re
import stat
import subprocess
import sys
from pathlib import Path, PurePosixPath

from dokime.core.outcomes import Outcome, Report, ReportLimits
from dokime.core.repository import RefusalError

READER_PROGRAM = Path(__file__).with_name("reader_process.py")
"""The program that parses the report, in a process of its own."""

MINIMUM_EXPAT = (2, 8, 5)
"""Expat 2.8.5 fixed CVE-2026-93990, malformed UTF-16, which a report only has to declare.

The entries of the `Changes` file of Expat behind this value are in the basis of ADR-0045.
"""

_EXPAT_VERSION = re.compile(r"expat_(\d+)\.(\d+)\.(\d+)")
_LAST_ERROR = 2000
"""How much of what the program that reads wrote on its error output a refusal quotes."""

_OUTCOMES = {outcome.value: outcome for outcome in Outcome}


def expat_version() -> str:
    """Give the version of the Expat that parses the reports, refusing one older than the minimum.

    The program that reads runs on the same Python as the harness, so it has the same Expat.
    """
    found = _EXPAT_VERSION.fullmatch(pyexpat.EXPAT_VERSION)
    if found is None or tuple(int(part) for part in found.groups()) < MINIMUM_EXPAT:
        raise RefusalError(
            "expat-too-old",
            "the reader of reports needs Expat 2.8.5 or later, and the Python of the harness has"
            f" {pyexpat.EXPAT_VERSION.removeprefix('expat_')!r}",
        )
    return pyexpat.EXPAT_VERSION.removeprefix("expat_")


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
        done = subprocess.run(
            [
                sys.executable,
                "-I",
                str(READER_PROGRAM),
                str(descriptor),
                str(limits.report_bytes),
                str(limits.reader_memory_bytes),
                str(limits.reader_cpu_seconds),
            ],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            check=False,
            pass_fds=(descriptor,),
        )
    finally:
        os.close(descriptor)
    return _result(report, limits, done)


def _result(
    report: PurePosixPath, limits: ReportLimits, done: "subprocess.CompletedProcess[bytes]"
) -> Report:
    """Turn what the program that reads gave into the report, or into its refusal."""
    try:
        given = json.loads(done.stdout) if done.returncode == 0 else None
    except ValueError:
        given = None
    if isinstance(given, dict) and isinstance(given.get("refusal"), str):
        refused = _refusal(report, limits, given["refusal"], str(given.get("detail", "")))
        if refused is not None:
            raise refused
    cases = given.get("cases") if isinstance(given, dict) else None
    if isinstance(cases, dict) and all(
        isinstance(name, str) and outcome in _OUTCOMES for name, outcome in cases.items()
    ):
        return {name: _OUTCOMES[outcome] for name, outcome in cases.items()}
    ending = f"the signal {-done.returncode}" if done.returncode < 0 else f"{done.returncode}"
    raise RefusalError(
        "report-reader-failed",
        f"the process that reads the report {report} ended with {ending} and gave no report: "
        f"{done.stderr.decode(errors='replace').strip()[-_LAST_ERROR:] or 'no output'}",
    )


def _refusal(
    report: PurePosixPath, limits: ReportLimits, code: str, detail: str
) -> RefusalError | None:
    messages = {
        "report-too-large": (
            f"the report {report} is larger than its limit of {limits.report_bytes} bytes"
        ),
        "report-has-doctype": f"the report {report} has a DOCTYPE",
        "report-unreadable": f"the report {report} is not well-formed XML: {detail}",
        "report-duplicate-test": f"the report names the test {detail!r} twice",
    }
    return RefusalError(code, messages[code]) if code in messages else None
