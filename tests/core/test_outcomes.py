# SDD-EARS: CORE-074 CORE-075 CORE-076 CORE-077 CORE-078
from typing import get_type_hints

import pytest

from dokime.core.outcomes import Outcome, Report, ReportLimits

MIB = 1024 * 1024


def test_the_outcome_of_a_test_is_one_of_four() -> None:
    assert {outcome.value for outcome in Outcome} == {"passed", "failed", "error", "skipped"}


def test_a_report_gives_the_outcome_of_each_test_by_its_name() -> None:
    report: Report = {"tests/test_a.py::test_one": Outcome.PASSED}
    assert report["tests/test_a.py::test_one"] is Outcome.PASSED
    assert Report.__value__.__args__ == (str, Outcome)


def test_the_limits_carry_the_size_the_memory_and_the_processor_time() -> None:
    limits = ReportLimits(report_bytes=1, reader_memory_bytes=2, reader_cpu_seconds=3)
    assert (limits.report_bytes, limits.reader_memory_bytes, limits.reader_cpu_seconds) == (1, 2, 3)
    assert set(get_type_hints(ReportLimits).values()) == {int}


def test_the_limits_default_to_32_mib_512_mib_and_10_seconds() -> None:
    limits = ReportLimits()
    assert (limits.report_bytes, limits.reader_memory_bytes, limits.reader_cpu_seconds) == (
        32 * MIB,
        512 * MIB,
        10,
    )


@pytest.mark.parametrize("field", ["report_bytes", "reader_memory_bytes", "reader_cpu_seconds"])
@pytest.mark.parametrize("value", [0, -1, 1.5, True])
def test_a_limit_that_is_not_a_whole_number_above_zero_is_rejected_naming_it(
    field: str, value: object
) -> None:
    with pytest.raises(ValueError, match=field):
        ReportLimits(**{field: value})  # type: ignore[arg-type]
