"""The rules of the self-check of a pack, as decisions over reports obtained elsewhere."""

from collections.abc import Iterable, Mapping, Sequence
from enum import StrEnum, auto

from dokime.core.findings import Finding
from dokime.core.verdicts import Verdict
from dokime.packs.model import Pack

WITNESSES_NEEDED = 2
CANDIDATES_LOOKED_AT = 10


class Outcome(StrEnum):
    """What happened to one test in one run."""

    PASSED = auto()
    FAILED = auto()
    ERROR = auto()
    SKIPPED = auto()


type Report = Mapping[str, Outcome]


def is_candidate(pack: Pack, changed: Iterable[str]) -> bool:
    """Say whether a commit that changed these paths may prove the pack.

    It may when it changed a test and code that is not a test: a fix that came with its test.
    """
    are_tests = {pack.is_test(path) for path in changed}
    return are_tests == {True, False}


def is_witness(parent: Report, commit: Report) -> bool:
    """Say whether the reports of a candidate prove that the pack runs its tests.

    They do when a test passes on the commit and did not pass on the parent, where something
    failed. A parent report in which nothing fails proves nothing: the run may have done nothing.
    """
    broken = (Outcome.FAILED, Outcome.ERROR)
    if not any(outcome in broken for outcome in parent.values()):
        return False
    return any(
        outcome is Outcome.PASSED and parent.get(test) in (*broken, None)
        for test, outcome in commit.items()
    )


def self_check(candidates: Sequence[bool]) -> tuple[Finding, ...]:
    """Decide the self-check from which candidates, in order, were witnesses."""
    looked_at = candidates[:CANDIDATES_LOOKED_AT]
    witnesses = sum(looked_at)
    if witnesses >= WITNESSES_NEEDED:
        return ()
    message = (
        f"{witnesses} of {len(looked_at)} candidates prove that the pack runs the tests; "
        f"{WITNESSES_NEEDED} are needed among the first {CANDIDATES_LOOKED_AT}"
    )
    return (Finding(code="too-few-witnesses", message=message, verdict=Verdict.FAIL),)
