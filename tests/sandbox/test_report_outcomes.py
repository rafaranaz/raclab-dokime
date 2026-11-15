# SDD-EARS: SANDBOX-040 SANDBOX-041
from pathlib import Path, PurePosixPath

import pytest

from dokime.core.outcomes import Outcome, ReportLimits
from dokime.sandbox.report import read_report
from tests.sandbox.engines import Engine

REPORT = b"""<?xml version="1.0" encoding="utf-8"?>
<testsuites name="pytest tests">
  <testsuite name="pytest" errors="1" failures="1" skipped="1" tests="5">
    <testcase classname="tests.test_a" name="test_passes" time="0.001" />
    <testcase classname="tests.test_a" name="test_fails" time="0.001">
      <failure message="assert 1 == 2">the trace</failure>
    </testcase>
    <testcase classname="tests.test_b.TestIt" name="test_errors[case-1]" time="0.001">
      <error message="fixture broke">the trace</error>
    </testcase>
    <testcase classname="tests.test_b.TestIt" name="test_skipped" time="0.000">
      <skipped type="pytest.skip" message="not here">the reason</skipped>
    </testcase>
    <testcase classname="tests.test_c" name="test_with_output" time="0.001">
      <system-out>printed</system-out>
    </testcase>
  </testsuite>
</testsuites>
"""


@pytest.fixture
def out(tmp_path: Path) -> Path:
    (tmp_path / "reports").mkdir()
    (tmp_path / "reports" / "report.xml").write_bytes(REPORT)
    return tmp_path


def test_each_test_case_is_named_by_its_class_name_and_its_name(out: Path) -> None:
    report = read_report(out, PurePosixPath("reports/report.xml"), ReportLimits())
    assert set(report) == {
        "tests.test_a::test_passes",
        "tests.test_a::test_fails",
        "tests.test_b.TestIt::test_errors[case-1]",
        "tests.test_b.TestIt::test_skipped",
        "tests.test_c::test_with_output",
    }


def test_each_test_case_has_the_outcome_its_children_say(out: Path) -> None:
    report = read_report(out, PurePosixPath("reports/report.xml"), ReportLimits())
    assert report == {
        "tests.test_a::test_passes": Outcome.PASSED,
        "tests.test_a::test_fails": Outcome.FAILED,
        "tests.test_b.TestIt::test_errors[case-1]": Outcome.ERROR,
        "tests.test_b.TestIt::test_skipped": Outcome.SKIPPED,
        "tests.test_c::test_with_output": Outcome.PASSED,
    }


def test_a_bare_testsuite_is_read_like_one_inside_testsuites(tmp_path: Path) -> None:
    (tmp_path / "r.xml").write_bytes(
        b'<testsuite><testcase classname="t" name="one"><failure/></testcase></testsuite>'
    )
    assert read_report(tmp_path, PurePosixPath("r.xml"), ReportLimits()) == {
        "t::one": Outcome.FAILED
    }


def test_the_adapter_reads_a_report_as_the_shared_reader_does(out: Path, engine: Engine) -> None:
    path, limits = PurePosixPath("reports/report.xml"), ReportLimits()
    assert engine.adapter().read_report(out, path, limits) == read_report(out, path, limits)
