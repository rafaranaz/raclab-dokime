# SDD-EARS: SANDBOX-060 SANDBOX-061 SANDBOX-064
import os
import subprocess
import textwrap
from pathlib import Path, PurePosixPath

import pytest

from dokime.core.outcomes import Outcome, ReportLimits
from dokime.sandbox import report
from dokime.sandbox.report import read_report
from tests.sandbox.engines import refusal

REPORT = b'<testsuite><testcase classname="t" name="one"/></testsuite>'

WRAPPER = """\
import importlib.util
import sys

spec = importlib.util.spec_from_file_location("reader", {real!r})
reader = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reader)
{replacement}
reader.main(sys.argv)
"""


def reader_whose_read_is(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, replacement: str) -> None:
    """Run the real program that reads, with its parsing replaced, so its limits still apply."""
    program = tmp_path / "reader.py"
    program.write_text(
        WRAPPER.format(real=str(report.READER_PROGRAM), replacement=textwrap.dedent(replacement))
    )
    monkeypatch.setattr(report, "READER_PROGRAM", program)


def written(tmp_path: Path) -> PurePosixPath:
    (tmp_path / "report.xml").write_bytes(REPORT)
    return PurePosixPath("report.xml")


def test_a_reader_that_crashes_leaves_the_harness_running_and_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    reader_whose_read_is(
        tmp_path, monkeypatch, "import ctypes\nreader.read = lambda *_: ctypes.string_at(0)"
    )
    finding = refusal(lambda: read_report(tmp_path, written(tmp_path), ReportLimits()))
    assert finding.code == "report-reader-failed"


@pytest.mark.parametrize(
    "replacement",
    [
        "reader.read = lambda *_: sys.exit(0)",
        "reader.read = lambda *_: sys.exit(3)",
        "reader.read = lambda *_: 'not a result'",
    ],
    ids=["no-output", "failed", "not-a-result"],
)
def test_a_reader_that_ends_without_giving_a_report_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, replacement: str
) -> None:
    reader_whose_read_is(tmp_path, monkeypatch, replacement)
    finding = refusal(lambda: read_report(tmp_path, written(tmp_path), ReportLimits()))
    assert finding.code == "report-reader-failed"


def test_the_real_reader_gives_the_report(tmp_path: Path) -> None:
    assert read_report(tmp_path, written(tmp_path), ReportLimits()) == {"t::one": Outcome.PASSED}


def test_a_report_replaced_after_the_adapter_opened_it_is_read_as_it_was(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = written(tmp_path)
    other = tmp_path / "other.xml"
    other.write_bytes(b'<testsuite><testcase classname="t" name="other"/></testsuite>')
    start = subprocess.run

    def replace_then_start(*args: object, **kwargs: object) -> object:
        os.replace(other, tmp_path / "report.xml")
        return start(*args, **kwargs)  # type: ignore[call-overload]

    monkeypatch.setattr(subprocess, "run", replace_then_start)
    assert read_report(tmp_path, path, ReportLimits()) == {"t::one": Outcome.PASSED}
