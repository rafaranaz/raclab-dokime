# SDD-EARS: SANDBOX-048 SANDBOX-049
import contextlib
import os
import threading
from pathlib import Path, PurePosixPath

import pytest

from dokime.core.outcomes import Outcome, ReportLimits
from dokime.sandbox.report import read_report
from tests.sandbox.engines import refusal

REPORT = b'<testsuite><testcase classname="t" name="one"/></testsuite>'


def output_with_report(tmp_path: Path) -> Path:
    out = tmp_path / "out"
    (out / "real").mkdir(parents=True)
    (out / "real" / "report.xml").write_bytes(REPORT)
    (out / "real.xml").write_bytes(REPORT)
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    (elsewhere / "report.xml").write_bytes(REPORT)
    return out


@pytest.mark.parametrize(
    ("link", "target", "given"),
    [
        ("sub", "../elsewhere", "sub/report.xml"),
        ("sub", "real", "sub/report.xml"),
        ("report.xml", "real.xml", "report.xml"),
    ],
    ids=["directory-outside", "directory-inside", "the-report"],
)
def test_a_link_in_the_path_of_the_report_is_refused_naming_the_path(
    tmp_path: Path, link: str, target: str, given: str
) -> None:
    out = output_with_report(tmp_path)
    (out / link).symlink_to(target)
    finding = refusal(lambda: read_report(out, PurePosixPath(given), ReportLimits()))
    assert (finding.code, given in finding.message) == ("report-not-a-file", True)


def test_the_same_report_without_a_link_is_read(tmp_path: Path) -> None:
    out = output_with_report(tmp_path)
    assert read_report(out, PurePosixPath("real/report.xml"), ReportLimits()) == {
        "t::one": Outcome.PASSED
    }


def test_a_report_that_is_a_directory_is_refused_naming_the_path(tmp_path: Path) -> None:
    (tmp_path / "report.xml").mkdir()
    finding = refusal(lambda: read_report(tmp_path, PurePosixPath("report.xml"), ReportLimits()))
    assert (finding.code, "report.xml" in finding.message) == ("report-not-a-file", True)


def test_a_report_that_is_a_fifo_is_refused_naming_the_path(tmp_path: Path) -> None:
    fifo = tmp_path / "report.xml"
    os.mkfifo(fifo)

    def release_a_blocked_reader() -> None:
        """Open the other end later, so that a reader blocked on the FIFO does not hang."""
        threading.Event().wait(5)
        with contextlib.suppress(OSError):
            os.close(os.open(fifo, os.O_WRONLY | os.O_NONBLOCK))

    threading.Thread(target=release_a_blocked_reader, daemon=True).start()
    finding = refusal(lambda: read_report(tmp_path, PurePosixPath("report.xml"), ReportLimits()))
    assert (finding.code, "report.xml" in finding.message) == ("report-not-a-file", True)
