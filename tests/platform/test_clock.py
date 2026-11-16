# SDD-EARS: PLATFORM-070
from datetime import UTC, datetime

from dokime.platform.clock import SystemClock


def test_the_clock_gives_the_time_of_the_system_in_utc() -> None:
    before = datetime.now(UTC)
    now = SystemClock().now()
    after = datetime.now(UTC)
    assert now.utcoffset() is not None
    assert now.utcoffset().total_seconds() == 0  # type: ignore[union-attr]
    assert before <= now <= after
