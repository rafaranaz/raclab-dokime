# SDD-EARS: CONTRACT-095 CONTRACT-096 CONTRACT-097 CONTRACT-098
import pytest

from dokime.contract.check import check
from dokime.contract.model import Checked
from dokime.core.verdicts import Verdict
from tests.contract.contracts import VALID, codes, line_of, only

RELATION = """\
  - id: L1
    requirement: round-total-once
    relation: order-insensitive
    target: billing.totals:invoice_total
    over: args[0]
"""
FUNCTION = "billing.totals:invoice_total"
CLI = "invoice total"


def relation(requirement: str = "round-total-once", **fields: str) -> str:
    lines = "".join(f"    {name}: {value}\n" for name, value in fields.items())
    return f"  - id: L1\n    requirement: {requirement}\n" + lines


def with_relation(text: str, contract: str = VALID) -> Checked:
    """The check of the valid contract with its relation replaced."""
    assert contract.count(RELATION) == 1
    return check(contract.replace(RELATION, text))


def test_the_relation_of_the_valid_contract_has_no_finding() -> None:
    result = check(VALID)
    assert codes(result) == []
    assert result.contract is not None
    (found,) = result.contract.relations
    assert (found.over, found.via) == ("args[0]", None)


def test_a_relation_whose_target_no_visible_example_has_asks() -> None:
    result = with_relation(relation(relation="idempotent", target="billing.totals:nowhere"))
    finding = only(result, "relation-without-example")
    assert finding.verdict is Verdict.ASK
    assert finding.lines == (line_of(RELATION),)
    assert result.contract is not None


def test_a_relation_whose_examples_are_at_two_boundaries_is_refused() -> None:
    both = VALID.replace(f"    target: {CLI}\n", f"    target: {FUNCTION}\n")
    result = with_relation(relation(relation="idempotent", target=FUNCTION, over="args[0]"), both)
    assert only(result, "relation-target-ambiguous").verdict is Verdict.FAIL


def test_idempotent_at_cli_needs_its_channel() -> None:
    finding = only(with_relation(relation(relation="idempotent", target=CLI)), "relation-needs-via")
    assert finding.lines == (line_of(RELATION),)


@pytest.mark.parametrize("via", ["stdout", "files"])
def test_idempotent_at_cli_with_its_channel_has_no_finding(via: str) -> None:
    result = with_relation(relation(relation="idempotent", target=CLI, via=via))
    assert codes(result) == []
    assert result.contract is not None
    assert result.contract.relations[0].via == via


def test_a_channel_outside_its_list_is_an_unknown_value() -> None:
    result = with_relation(relation(relation="idempotent", target=CLI, via="stderr"))
    assert codes(result) == ["unknown-value"]


def test_a_channel_of_idempotent_at_a_function_is_refused() -> None:
    text = relation(relation="idempotent", target=FUNCTION, over="args[0]", via="stdout")
    only(with_relation(text), "relation-via-not-allowed")


def test_a_channel_on_order_insensitive_is_not_a_field_of_it() -> None:
    text = relation(relation="order-insensitive", target=CLI, over="stdin", via="stdout")
    assert codes(with_relation(text)) == ["unknown-field"]
