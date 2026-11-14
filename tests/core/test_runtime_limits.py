# SDD-EARS: CORE-090 CORE-091 CORE-092 CORE-093 CORE-094 CORE-095
import math
from typing import get_type_hints

import pytest

from dokime.core.runtime import BuildLimits, RunLimits

GIB = 1024 * 1024 * 1024


def test_the_limits_of_a_build_carry_the_time_on_the_clock() -> None:
    assert BuildLimits(time_seconds=60).time_seconds == 60
    assert get_type_hints(BuildLimits) == {"time_seconds": int}


def test_the_limits_of_a_build_default_to_1800_seconds() -> None:
    assert BuildLimits().time_seconds == 1800


@pytest.mark.parametrize("value", [0, -1, 1.5, True, math.inf, math.nan])
def test_a_build_time_that_is_not_a_whole_number_above_zero_is_rejected_naming_it(
    value: object,
) -> None:
    with pytest.raises(ValueError, match="time_seconds"):
        BuildLimits(time_seconds=value)  # type: ignore[arg-type]


def test_the_limits_of_a_run_carry_memory_processors_processes_and_time() -> None:
    limits = RunLimits(memory_bytes=1, processors=0.5, processes=2, time_seconds=3)
    assert (limits.memory_bytes, limits.processors, limits.processes, limits.time_seconds) == (
        1,
        0.5,
        2,
        3,
    )


def test_the_limits_of_a_run_default_to_2_gib_2_processors_512_processes_and_900_seconds() -> None:
    limits = RunLimits()
    assert (limits.memory_bytes, limits.processors, limits.processes, limits.time_seconds) == (
        2 * GIB,
        2,
        512,
        900,
    )


@pytest.mark.parametrize("field", ["memory_bytes", "processes", "time_seconds"])
@pytest.mark.parametrize("value", [0, -1, 1.5, True, math.inf, math.nan])
def test_a_whole_limit_of_a_run_that_is_not_a_whole_number_above_zero_is_rejected_naming_it(
    field: str, value: object
) -> None:
    with pytest.raises(ValueError, match=field):
        RunLimits(**{field: value})  # type: ignore[arg-type]


@pytest.mark.parametrize("value", [0, -0.5, True, False, math.inf, -math.inf, math.nan, "2"])
def test_processors_that_are_not_a_finite_number_above_zero_are_rejected_naming_them(
    value: object,
) -> None:
    with pytest.raises(ValueError, match="processors"):
        RunLimits(processors=value)  # type: ignore[arg-type]


@pytest.mark.parametrize("value", [0.5, 1, 1.25])
def test_processors_may_be_a_fraction_or_a_whole_number(value: float) -> None:
    assert RunLimits(processors=value).processors == value
