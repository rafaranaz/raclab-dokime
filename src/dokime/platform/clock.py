"""The clock of the system."""

from datetime import UTC, datetime


class SystemClock:
    """Gives the time of the system."""

    def now(self) -> datetime:
        """The current time, in UTC."""
        return datetime.now(UTC)
