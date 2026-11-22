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
    """A step at `function` raised an exception: the name of its class, its full name, the full
    names of the classes of its MRO, from its own to `object`, and its message.

    The full names tell a class of the project from one of Python with the same name. The field
    is `classes`, not `mro`, which a dataclass would take for the method of `type`.
    """

    type: str
    qualified: str
    classes: tuple[str, ...]
    message: str


REPR_LIMIT = 1000
"""The characters of the `repr` of a value that JSON cannot hold that an observation keeps."""


@dataclass(frozen=True)
class NotJson:
    """A step at `function` returned a value that JSON cannot hold: the name of its type and its
    `repr`, cut to its first characters, and marked so, when it is longer than the limit
    (ADR-0079). An adapter that did not record the `repr` leaves it as `None`."""

    type: str
    representation: str | None = None
    cut: bool = False

    def __post_init__(self) -> None:
        length = len(self.representation or "")
        if length > REPR_LIMIT:
            raise ValueError(f"the representation has {length} characters, more than {REPR_LIMIT}")
        if self.cut and length < REPR_LIMIT:
            raise ValueError(f"the representation is marked cut with only {length} characters")


def not_json(type_name: str, representation: str) -> NotJson:
    """The observation of a value that JSON cannot hold, with its `repr` within the limit."""
    cut = len(representation) > REPR_LIMIT
    return NotJson(type=type_name, representation=representation[:REPR_LIMIT], cut=cut)


@dataclass(frozen=True)
class Exited:
    """A step at `cli`: its exit code, its output, its error and the files it wrote."""

    exit: int
    stdout: str
    stderr: str
    files: Mapping[str, str] = field(default_factory=dict)


type StepObservation = Returned | Raised | NotJson | Exited


class Ending(StrEnum):
    """How an example ended."""

    COMPLETED = "completed"
    TIME_LIMIT = "time-limit"
    OUTPUT_LIMIT = "output-limit"
    CRASHED = "crashed"


@dataclass(frozen=True)
class ExampleObservation:
    """What the zone saw of one example: each step that ran, and how it ended; a crash carries the
    signal or the exit code of its process, when they are known."""

    example: str
    steps: tuple[StepObservation, ...]
    ending: Ending = Ending.COMPLETED
    signal: int | None = None
    exit_code: int | None = None

    def __post_init__(self) -> None:
        if self.ending is not Ending.CRASHED:
            for name in ("signal", "exit_code"):
                if getattr(self, name) is not None:
                    raise ValueError(f"an example that did not crash carries no {name}")


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
