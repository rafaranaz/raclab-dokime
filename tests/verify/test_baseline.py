# SDD-EARS: VERIFY-040 VERIFY-041 VERIFY-042 VERIFY-043 VERIFY-060 VERIFY-061 VERIFY-062
import pytest

from dokime.core.observation import Boundary, ExampleRequest
from dokime.core.verdicts import Verdict
from tests.verify.gates import codes, contract, example, on_base, on_change


def test_the_examples_are_observed_on_the_base_in_their_order_without_their_expectations() -> None:
    given = contract(example("E-2", "R-new"), example("E-1", "R-keep"))
    _, observer = on_base(given, {"E-1": 2})
    ((files, requests),) = observer.calls
    assert files == {"answers.json": '{"E-1": 2}', "src/p.py": "code"}
    assert requests == tuple(
        ExampleRequest(
            example=name, boundary=Boundary.FUNCTION, target="p:f", inputs=({"args": [1]},)
        )
        for name in ("E-2", "E-1")
    )


@pytest.mark.parametrize("run", [on_base, on_change], ids=["baseline", "visible-examples"])
def test_a_contract_without_examples_passes_without_observing(run: object) -> None:
    assert callable(run)
    findings, observer = run(contract(), {})
    assert (findings, observer.calls) == ([], [])


def test_a_preserved_example_that_holds_on_the_base_passes() -> None:
    assert on_base(contract(example("E-1", "R-keep")), {"E-1": 2})[0] == []


def test_a_preserved_example_that_fails_on_the_base_fails() -> None:
    (found,) = on_base(contract(example("E-1", "R-keep", line=14)), {"E-1": 3})[0]
    assert codes([found]) == [("preserved-example-fails-on-base", Verdict.FAIL)]
    assert found.lines == (14,)
    assert all(part in found.message for part in ("E-1", "R-keep", "returns", "2", "3"))


@pytest.mark.parametrize("requirement", ["R-new", "R-change"])
def test_a_new_or_changed_example_that_fails_on_the_base_passes(requirement: str) -> None:
    assert on_base(contract(example("E-1", requirement)), {"E-1": 3})[0] == []


@pytest.mark.parametrize("requirement", ["R-new", "R-change"])
def test_a_new_or_changed_example_that_already_holds_on_the_base_asks(requirement: str) -> None:
    (found,) = on_base(contract(example("E-1", requirement)), {"E-1": 2})[0]
    assert codes([found]) == [("example-holds-on-base", Verdict.ASK)]
    assert "E-1" in found.message
    assert requirement in found.message


def test_a_refusal_of_the_repository_on_the_base_is_an_error() -> None:
    (found,) = on_base(contract(example("E-1", "R-keep")), {"E-1": 2}, missing_base=True)[0]
    assert codes([found]) == [("commit-missing", Verdict.ERROR)]
