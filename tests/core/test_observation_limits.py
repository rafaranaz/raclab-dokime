# SDD-EARS: CORE-166 CORE-167 CORE-168
import pytest

from dokime.core.observation import ObservationLimits
from dokime.core.runtime import RunLimits


def test_the_limits_default_to_sixty_seconds_and_thirty_two_mebibytes() -> None:
    limits = ObservationLimits()
    assert (limits.example_seconds, limits.observations_bytes) == (60, 32 * 1024 * 1024)
    assert limits.run == RunLimits()


@pytest.mark.parametrize("name", ["example_seconds", "observations_bytes"])
@pytest.mark.parametrize("value", [0, -1, 1.5, True, "60"])
def test_a_limit_that_is_not_a_whole_number_above_zero_is_rejected_naming_it(
    name: str, value: object
) -> None:
    with pytest.raises(ValueError, match=name):
        ObservationLimits(**{name: value})  # type: ignore[arg-type]
