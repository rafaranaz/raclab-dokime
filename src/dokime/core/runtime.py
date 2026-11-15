"""The port of the verification runtime and the values it exchanges.

`core` defines what the port gives and takes; it runs no engine. The port says how a run ended and
decides no verdict: the module that called it does. An adapter that cannot do an operation raises
the same `RefusalError` as an adapter of the project repository.
"""

import math
import re
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path, PurePosixPath
from typing import Protocol

from dokime.core.outcomes import Report, ReportLimits
from dokime.core.repository import RefusalError

__all__ = [
    "BaseImage",
    "Build",
    "BuildLimits",
    "Digest",
    "Ending",
    "RefusalError",
    "RunLimits",
    "RunResult",
    "VerificationRuntime",
]

_DIGEST = re.compile(r"sha256:[0-9a-f]{64}")
_GIB = 1024 * 1024 * 1024


@dataclass(frozen=True)
class Digest:
    """The digest of an image or of a manifest: `sha256:` and 64 lowercase hexadecimal digits."""

    text: str

    def __post_init__(self) -> None:
        if not _DIGEST.fullmatch(self.text):
            raise ValueError(
                f"the digest {self.text!r} is not 'sha256:' followed by 64 lowercase hexadecimal"
                " characters"
            )


@dataclass(frozen=True)
class BaseImage:
    """The image a stage starts from, by the digest of the manifest of the platform built."""

    platform: Digest


@dataclass(frozen=True)
class Build:
    """What a build gives: the image built, and the base image of the final stage, if any."""

    image: Digest
    base: BaseImage | None


class Ending(StrEnum):
    """How a run ended."""

    EXITED = "exited"
    TIME_LIMIT = "time-limit"
    MEMORY_LIMIT = "memory-limit"
    KILLED = "killed"


@dataclass(frozen=True)
class RunResult:
    """How a run ended, and the exit code of the command when it exited by itself."""

    ending: Ending
    exit_code: int | None

    def __post_init__(self) -> None:
        if self.ending is Ending.EXITED and self.exit_code is None:
            raise ValueError("a run that exited by itself needs its exit code")
        if self.ending is not Ending.EXITED and self.exit_code is not None:
            raise ValueError(
                f"a run that ended as {self.ending.value!r} has no exit code, not {self.exit_code}"
            )


def _check_whole(name: str, value: object) -> None:
    if type(value) is not int or value < 1:
        raise ValueError(f"the limit {name} is {value!r}, not a whole number greater than zero")


@dataclass(frozen=True)
class BuildLimits:
    """How long a build may take on the clock. The module that calls the runtime passes it."""

    time_seconds: int = 1800

    def __post_init__(self) -> None:
        _check_whole("time_seconds", self.time_seconds)


@dataclass(frozen=True)
class RunLimits:
    """How much a run may take. The module that calls the runtime passes it; a pack cannot."""

    memory_bytes: int = 2 * _GIB
    processors: float = 2
    processes: int = 512
    time_seconds: int = 900

    def __post_init__(self) -> None:
        _check_whole("memory_bytes", self.memory_bytes)
        _check_whole("processes", self.processes)
        _check_whole("time_seconds", self.time_seconds)
        cpus = self.processors
        if type(cpus) not in (int, float) or not math.isfinite(cpus) or cpus <= 0:
            raise ValueError(
                f"the limit processors is {cpus!r}, not a finite number greater than zero"
            )


class VerificationRuntime(Protocol):
    """The port of the verification runtime. Every operation may raise a `RefusalError`."""

    def build(self, dockerfile: Path, directory: Path, limits: BuildLimits) -> Build:
        """Build an image from a Dockerfile and the directory it builds from."""
        ...

    def run(
        self,
        image: Digest,
        command: tuple[str, ...],
        project: Path,
        output: Path,
        limits: RunLimits,
    ) -> RunResult:
        """Run a command in an image, with the project and the output directory mounted."""
        ...

    def read_report(self, output: Path, report: PurePosixPath, limits: ReportLimits) -> Report:
        """Read the report that a run wrote at `report` inside the output directory."""
        ...
