"""The verdict of a gate and the aggregation of the verdicts of a round."""

from collections.abc import Iterable
from enum import StrEnum, auto


class Verdict(StrEnum):
    """What a gate returns. The value of each verdict is its name."""

    @staticmethod
    def _generate_next_value_(name: str, start: int, count: int, last_values: list[str]) -> str:
        return name

    PASS = auto()
    FAIL = auto()
    ASK = auto()
    ERROR = auto()


class EmptyRoundError(ValueError):
    """Raised when a round with no verdicts is aggregated."""


def aggregate(verdicts: Iterable[Verdict]) -> Verdict:
    """Return the verdict of a round from the verdicts of its gates.

    The first of `ERROR`, `FAIL` and `ASK` that is present decides; a round of `PASS` passes.
    """
    present = set(verdicts)
    if not present:
        raise EmptyRoundError("the round is empty: no gate returned a verdict")
    for verdict in (Verdict.ERROR, Verdict.FAIL, Verdict.ASK):
        if verdict in present:
            return verdict
    return Verdict.PASS
