# SDD-EARS: SANDBOX-040 SANDBOX-041 SANDBOX-042 SANDBOX-043 SANDBOX-044 SANDBOX-046 SANDBOX-061
"""The program that reads a report, called inside the process of the tests.

The tests of `read_report` run it in its own process, which coverage does not measure, so these
call it here, on a descriptor as the adapter passes it. `bound` is not called here: it would limit
the process of the tests.
"""

import json
import os
from pathlib import Path

import pytest

from dokime.sandbox import reader_process

CASES = (
    b'<testsuite><testcase classname="t" name="passes"/>'
    b'<testcase classname="t" name="fails"><failure/></testcase>'
    b'<testcase classname="t" name="errs"><failure/><error/></testcase>'
    b'<testcase classname="t" name="skips"><skipped/></testcase></testsuite>'
)


def opened(tmp_path: Path, data: bytes) -> int:
    """Open a report as the adapter does, and give its descriptor."""
    (tmp_path / "report.xml").write_bytes(data)
    return os.open(tmp_path / "report.xml", os.O_RDONLY)


def test_it_gives_each_case_with_its_outcome(tmp_path: Path) -> None:
    assert reader_process.read(opened(tmp_path, CASES), 1024) == {
        "cases": {
            "t::passes": "passed",
            "t::fails": "failed",
            "t::errs": "error",
            "t::skips": "skipped",
        }
    }


@pytest.mark.parametrize(
    ("data", "limit", "code"),
    [
        (CASES, len(CASES) - 1, "report-too-large"),
        (b"<!DOCTYPE t><testsuite/>", 1024, "report-has-doctype"),
        (b"<testsuite>", 1024, "report-unreadable"),
        (
            b'<s><testcase classname="t" name="a"/><testcase classname="t" name="a"/></s>',
            1024,
            "report-duplicate-test",
        ),
    ],
    ids=["too-large", "doctype", "not-well-formed", "duplicate"],
)
def test_it_gives_the_refusal_of_a_report(
    tmp_path: Path, data: bytes, limit: int, code: str
) -> None:
    assert reader_process.read(opened(tmp_path, data), limit)["refusal"] == code


def test_main_bounds_the_process_before_it_reads_and_writes_the_result(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    calls: list[object] = []
    read = reader_process.read

    def bound(memory: int, processor: int) -> None:
        calls.append(("bound", (memory, processor)))

    def spied(descriptor: int, limit: int) -> dict[str, object]:
        calls.append("read")
        return read(descriptor, limit)

    monkeypatch.setattr(reader_process, "bound", bound)
    monkeypatch.setattr(reader_process, "read", spied)
    descriptor = opened(tmp_path, CASES)
    reader_process.main(["reader", str(descriptor), "1024", str(64 * 1024 * 1024), "10"])
    assert calls == [("bound", (64 * 1024 * 1024, 10)), "read"]
    assert json.loads(capsys.readouterr().out)["cases"]["t::fails"] == "failed"
