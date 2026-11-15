# SDD-EARS: SANDBOX-042 SANDBOX-043 SANDBOX-044 SANDBOX-045 SANDBOX-046 SANDBOX-047
import tracemalloc
from pathlib import Path, PurePosixPath

import pytest

from dokime.core.outcomes import Outcome, ReportLimits
from dokime.sandbox.report import read_report
from tests.sandbox.engines import refusal

CASE = b'<testcase classname="t" name="one"/>'


def written(tmp_path: Path, data: bytes) -> PurePosixPath:
    (tmp_path / "report.xml").write_bytes(data)
    return PurePosixPath("report.xml")


def test_a_report_larger_than_its_limit_is_refused_reading_no_more_than_the_limit_and_a_byte(
    tmp_path: Path,
) -> None:
    huge = tmp_path / "report.xml"
    with huge.open("wb") as handle:
        handle.truncate(1024 * 1024 * 1024)
    limits = ReportLimits(report_bytes=1024 * 1024)
    tracemalloc.start()
    try:
        finding = refusal(lambda: read_report(tmp_path, PurePosixPath("report.xml"), limits))
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    assert finding.code == "report-too-large"
    assert peak < 4 * limits.report_bytes


def test_a_report_of_exactly_its_limit_is_read(tmp_path: Path) -> None:
    data = b"<testsuite>" + CASE + b"</testsuite>"
    path = written(tmp_path, data)
    assert read_report(tmp_path, path, ReportLimits(report_bytes=len(data))) == {
        "t::one": Outcome.PASSED
    }
    finding = refusal(lambda: read_report(tmp_path, path, ReportLimits(report_bytes=len(data) - 1)))
    assert finding.code == "report-too-large"


@pytest.mark.parametrize(
    "doctype",
    [
        b"<!DOCTYPE testsuite>",
        b'<!DOCTYPE t [<!ENTITY a "aaaaaaaaaa"><!ENTITY b "&a;&a;&a;&a;">]>',
        b'<!DOCTYPE t [<!ENTITY x SYSTEM "file:///etc/passwd">]>',
        b'<!DOCTYPE t SYSTEM "http://127.0.0.1:9/external.dtd">',
    ],
)
def test_a_report_with_a_doctype_is_refused(tmp_path: Path, doctype: bytes) -> None:
    path = written(
        tmp_path, b'<?xml version="1.0"?>' + doctype + b"<testsuite>" + CASE + b"</testsuite>"
    )
    assert refusal(lambda: read_report(tmp_path, path, ReportLimits())).code == "report-has-doctype"


@pytest.mark.parametrize("data", [b"", b"<testsuite>", b"<testsuite></other>", b"not xml at all"])
def test_a_report_that_is_not_well_formed_is_refused(tmp_path: Path, data: bytes) -> None:
    path = written(tmp_path, data)
    assert refusal(lambda: read_report(tmp_path, path, ReportLimits())).code == "report-unreadable"


def test_a_report_that_does_not_exist_is_refused_naming_its_path(tmp_path: Path) -> None:
    finding = refusal(
        lambda: read_report(tmp_path, PurePosixPath("sub/report.xml"), ReportLimits())
    )
    assert (finding.code, "sub/report.xml" in finding.message) == ("report-missing", True)


def test_two_test_cases_with_the_same_name_are_refused_naming_it(tmp_path: Path) -> None:
    path = written(
        tmp_path, b"<testsuite>" + CASE + b"<testsuite>" + CASE + b"</testsuite></testsuite>"
    )
    finding = refusal(lambda: read_report(tmp_path, path, ReportLimits()))
    assert (finding.code, "t::one" in finding.message) == ("report-duplicate-test", True)


@pytest.mark.parametrize("given", ["/etc/hostname", "../report.xml", "reports/../../report.xml"])
def test_a_report_path_that_is_absolute_or_has_dot_dot_is_refused_naming_it(
    tmp_path: Path, given: str
) -> None:
    outside = tmp_path / "report.xml"
    outside.write_bytes(b"<testsuite>" + CASE + b"</testsuite>")
    out = tmp_path / "out"
    (out / "reports").mkdir(parents=True)
    finding = refusal(lambda: read_report(out, PurePosixPath(given), ReportLimits()))
    assert (finding.code, given in finding.message) == ("path-outside-output", True)
