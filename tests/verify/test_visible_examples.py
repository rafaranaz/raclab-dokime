# SDD-EARS: VERIFY-040 VERIFY-041 VERIFY-042 VERIFY-080 VERIFY-081 VERIFY-082
import pytest

from dokime.core.repository import RefusalError
from dokime.core.verdicts import Verdict
from tests.verify.doubles import ObserverDouble, patch
from tests.verify.gates import codes, contract, example, on_change


def test_the_examples_are_observed_on_the_base_with_the_patch() -> None:
    _, observer = on_change(contract(example("E-1", "R-new")), {"E-1": 2})
    ((files, _),) = observer.calls
    assert files == {"answers.json": '{"E-1": 2}', "src/p.py": "new"}


def test_an_example_that_holds_with_the_patch_passes() -> None:
    assert on_change(contract(example("E-1", "R-new")), {"E-1": 2})[0] == []


@pytest.mark.parametrize("origin", ["human", "derived"])
def test_an_example_that_fails_with_the_patch_fails_unless_its_origin_is_model(origin: str) -> None:
    (found,) = on_change(contract(example("E-1", "R-new", origin, line=21)), {"E-1": 5})[0]
    assert codes([found]) == [("example-fails", Verdict.FAIL)]
    assert found.lines == (21,)
    assert all(part in found.message for part in ("E-1", "R-new", "returns", "2", "5"))


def test_a_finding_quotes_each_value_within_200_characters() -> None:
    long = example("E-1", "R-new")
    (found,) = on_change(contract(long), {"E-1": 10**1000})[0]
    assert len(found.message) < 600
    assert "E-1" in found.message


def test_an_example_of_origin_model_that_fails_with_the_patch_asks() -> None:
    (found,) = on_change(contract(example("E-1", "R-new", "model")), {"E-1": 5})[0]
    assert codes([found]) == [("model-example-fails", Verdict.ASK)]


def test_each_failing_example_is_a_finding_of_its_own() -> None:
    given = contract(
        example("E-1", "R-new"), example("E-2", "R-new", "model"), example("E-3", "R-new")
    )
    found = on_change(given, {"E-2": 0, "E-3": 2})[0]
    assert codes(found) == [("example-fails", Verdict.FAIL), ("model-example-fails", Verdict.ASK)]


def test_a_refusal_of_the_port_that_observes_is_an_error() -> None:
    observer = ObserverDouble(refusal=RefusalError("observation-failed", "it died"))
    (found,) = on_change(contract(example("E-1", "R-new")), {}, observer)[0]
    assert codes([found]) == [("observation-failed", Verdict.ERROR)]


def test_a_patch_that_does_not_apply_is_an_error_and_nothing_is_observed() -> None:
    given = contract(example("E-1", "R-new"))
    found, observer = on_change(given, {}, changed=patch(removes=["src/missing.py"]))
    assert codes(found) == [("patch-does-not-apply", Verdict.ERROR)]
    assert observer.calls == []
