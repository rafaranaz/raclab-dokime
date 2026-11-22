# SDD-EARS: ORACLE-063 ORACLE-064
import pytest

from dokime.contract.expectations import Repr
from dokime.core.observation import REPR_LIMIT, NotJson, Returned, StepObservation, not_json
from dokime.oracle.compare import compare
from tests.oracle.examples import example, observed, raised

TEXT = "Version(major=1, minor=0, patch=0, prerelease=None, build=None)"


def test_a_value_json_cannot_hold_with_the_repr_expected_holds() -> None:
    assert compare(
        example("function", {"returns": Repr(TEXT)}), observed(not_json("Version", TEXT))
    ).holds


@pytest.mark.parametrize(
    "seen",
    [
        not_json("Version", TEXT.replace("1", "2")),
        NotJson("Version"),
        Returned(TEXT),
        raised("builtins", "TypeError"),
    ],
)
def test_a_step_that_did_not_give_the_repr_says_what_it_did_without_it(
    seen: StepObservation,
) -> None:
    (difference,) = compare(
        example("function", {"returns": Repr(TEXT)}), observed(seen)
    ).differences
    assert difference.part == "returns"
    assert "major=2" not in str(difference.observed)


def test_a_repr_that_was_cut_never_holds() -> None:
    text = "x" * REPR_LIMIT
    cut = not_json("Big", text + "y")
    assert cut.representation == text
    assert not compare(example("function", {"returns": Repr(text)}), observed(cut)).holds
