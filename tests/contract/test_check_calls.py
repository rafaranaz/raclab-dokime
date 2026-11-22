# SDD-EARS: CONTRACT-103 CONTRACT-104 CONTRACT-105 CONTRACT-106
import pytest

from tests.contract.contracts import line_of, only, seeded

E3_STEP = "      - input: {args: [[]]}\n        expect: {returns: {total: 0, currency: EUR}}"


def with_call(step: str) -> str:
    return f"{E3_STEP}\n{step}"


@pytest.mark.parametrize("name", ["items", "__len__", "__eq__", "get_info"])
def test_a_later_step_may_call_a_public_method(name: str) -> None:
    checked = seeded(
        E3_STEP, with_call(f"      - input: {{call: {name}}}\n        expect: {{returns: 0}}")
    )
    assert checked.findings == ()
    (e3,) = [e for e in checked.contract.examples if e.id == "E-0003"]  # type: ignore[union-attr]
    assert e3.steps[1].input == {"call": name}


def test_a_first_step_with_call_is_a_finding() -> None:
    new = (
        "      - input: {call: items, args: [[]]}\n"
        "        expect: {returns: {total: 0, currency: EUR}}"
    )
    assert only(seeded(E3_STEP, new), "call-in-first-step").lines == (line_of(E3_STEP),)


@pytest.mark.parametrize("name", ["not a name", "3", "[1]"])
def test_a_call_that_is_not_a_name_of_python_is_a_finding(name: str) -> None:
    step = f"      - input: {{call: '{name}'}}\n        expect: {{returns: 0}}"
    assert only(seeded(E3_STEP, with_call(step)), "wrong-type")


@pytest.mark.parametrize("name", ["_private", "__mangled", "_"])
def test_a_call_of_a_name_that_is_not_public_is_a_finding(name: str) -> None:
    step = f"      - input: {{call: {name}}}\n        expect: {{returns: 0}}"
    finding = only(seeded(E3_STEP, with_call(step)), "call-not-public")
    assert name in finding.message
