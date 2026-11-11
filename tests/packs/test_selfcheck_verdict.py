# SDD-EARS: PACKS-036
import pytest

from dokime.core.verdicts import Verdict
from dokime.packs.selfcheck import self_check


@pytest.mark.parametrize(
    ("candidates", "looked_at", "witnesses"),
    [
        ([], 0, 0),
        ([True], 1, 1),
        ([False, False, True], 3, 1),
        ([False] * 9 + [True, True, True], 10, 1),
        ([False] * 10 + [True, True], 10, 0),
    ],
)
def test_fewer_than_two_witnesses_among_the_first_ten_is_a_finding_with_the_counts(
    candidates: list[bool], looked_at: int, witnesses: int
) -> None:
    (finding,) = self_check(candidates)
    assert finding.code == "too-few-witnesses"
    assert finding.verdict is Verdict.FAIL
    assert f"{witnesses} of {looked_at} candidates" in finding.message
