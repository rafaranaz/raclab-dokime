"""The port that observes the examples in the zone of verification, and what it gives (ADR-0063).

The zone receives only the inputs of the steps of an example and gives back what it saw; the
harness compares that with what is expected, outside the zone (ADR-0012). The port is apart from
the port of the verification runtime, which the self-check of a pack uses.
"""

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Protocol

from dokime.core.runtime import Digest, RunLimits

_MIB = 1024 * 1024


class Boundary(StrEnum):
    """Where an example observes the code: a function of a module, or a command line."""

    FUNCTION = "function"
    CLI = "cli"


@dataclass(frozen=True)
class ExampleRequest:
    """What the zone receives of one example: its inputs, and nothing of what is expected."""

    example: str
    boundary: Boundary
    target: str
    inputs: tuple[Mapping[str, object], ...]


@dataclass(frozen=True)
class Returned:
    """A step at `function` returned a value that JSON holds; decimals are kept."""

    value: object


@dataclass(frozen=True)
class Raised:
    """A step at `function` raised an exception, with its type and its message."""

    type: str
    message: str


@dataclass(frozen=True)
class NotJson:
    """A step at `function` returned a value that JSON cannot hold; the name of its type."""

    type: str


@dataclass(frozen=True)
class Exited:
    """A step at `cli`: its exit code, its output, its error and the files it wrote."""

    exit: int
    stdout: str
    stderr: str
    files: Mapping[str, str] = field(default_factory=dict)


type StepObservation = Returned | Raised | NotJson | Exited


@dataclass(frozen=True)
class ExampleObservation:
    """What the zone saw of one example: each step that ran, and whether it reached its limit."""

    example: str
    steps: tuple[StepObservation, ...]
    time_limit: bool = False


@dataclass(frozen=True)
class ObservationLimits:
    """How long one example may take, how large its observations may be, and the run of all."""

    example_seconds: int = 60
    observations_bytes: int = 32 * _MIB
    run: RunLimits = field(default_factory=RunLimits)

    def __post_init__(self) -> None:
        for name in ("example_seconds", "observations_bytes"):
            value = getattr(self, name)
            if type(value) is not int or value < 1:
                raise ValueError(
                    f"the limit {name} is {value!r}, not a whole number greater than zero"
                )


class ExampleObserver(Protocol):
    """The port that observes the examples. Every operation may raise a `RefusalError`."""

    def observe(
        self,
        image: Digest,
        project: Path,
        requests: tuple[ExampleRequest, ...],
        limits: ObservationLimits,
    ) -> tuple[ExampleObservation, ...]:
        """Observe the examples of the requests in an image, with the project mounted."""
        ...
