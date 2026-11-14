"""The outcome of a test run, as the adapter of the verification runtime gives it."""

from collections.abc import Mapping
from dataclasses import dataclass, fields
from enum import StrEnum, auto

_MIB = 1024 * 1024


class Outcome(StrEnum):
    """What happened to one test in one run."""

    PASSED = auto()
    FAILED = auto()
    ERROR = auto()
    SKIPPED = auto()


type Report = Mapping[str, Outcome]


@dataclass(frozen=True)
class ReportLimits:
    """How much the reader of a report may take: the size of the report, and the memory and the
    processor time of the process that reads it. The module that calls the runtime passes them."""

    report_bytes: int = 32 * _MIB
    reader_memory_bytes: int = 512 * _MIB
    reader_cpu_seconds: int = 10

    def __post_init__(self) -> None:
        for field in fields(self):
            value = getattr(self, field.name)
            if type(value) is not int or value < 1:
                raise ValueError(
                    f"the limit {field.name} is {value!r}, not a whole number greater than zero"
                )
