"""The port of the clock: the current time, which `platform` gives from the system."""

from datetime import datetime
from typing import Protocol


class Clock(Protocol):
    """Gives the current time."""

    def now(self) -> datetime:
        """The current time, with its time zone."""
        ...
