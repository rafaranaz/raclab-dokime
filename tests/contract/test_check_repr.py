# SDD-EARS: CONTRACT-082 CONTRACT-102 CONTRACT-107 CONTRACT-108 CONTRACT-109
import pytest

from dokime.contract.expectations import Repr, holds
from tests.contract.contracts import line_of, only, seeded


def test_returns_may_be_a_repr() -> None:
    new = "        expect: {returns: {$repr: 'Version(major=1, minor=0, patch=0)'}}"
    assert seeded("        expect: {returns: {total: 0, currency: EUR}}", new).findings == ()


@pytest.mark.parametrize(
    "returns",
    ["[{$repr: 'x'}]", "{total: {$repr: 'x'}, currency: EUR}"],
)
def test_a_repr_inside_returns_is_a_finding(returns: str) -> None:
    new = f"        expect: {{returns: {returns}}}"
    old = "        expect: {returns: {total: 0, currency: EUR}}"
    assert only(seeded(old, new), "repr-out-of-place").lines == (line_of(old),)


def test_a_repr_with_a_memory_address_is_a_finding() -> None:
    new = "        expect: {returns: {$repr: '<cached <function f at 0x7f3a2c>>'}}"
    old = "        expect: {returns: {total: 0, currency: EUR}}"
    assert only(seeded(old, new), "repr-with-address").lines == (line_of(old),)


def test_a_repr_longer_than_an_observation_keeps_is_a_finding() -> None:
    old = "        expect: {returns: {total: 0, currency: EUR}}"
    assert seeded(old, f"        expect: {{returns: {{$repr: '{'x' * 1000}'}}}}").findings == ()
    finding = only(
        seeded(old, f"        expect: {{returns: {{$repr: '{'x' * 1001}'}}}}"), "repr-too-long"
    )
    assert "1000" in finding.message.replace(",", "")


@pytest.mark.parametrize("observed", ["x", 1, None, ["x"], {"x": 1}])
def test_a_repr_holds_for_no_value_of_json(observed: object) -> None:
    assert not holds(Repr("x"), observed)


def test_an_exact_value_and_a_repr_for_the_same_inputs_contradict() -> None:
    other = """\
  - id: E-0004
    requirement: keep-empty-invoices
    case: empty
    boundary: function
    target: billing.totals:invoice_total
    origin: human
    steps:
      - input: {args: [[]]}
        expect: {returns: {$repr: "Total(0)"}}
"""
    finding = only(seeded("\nrelations:", f"\n{other}\nrelations:"), "contradictory-examples")
    assert "E-0003" in finding.message
    assert "E-0004" in finding.message
