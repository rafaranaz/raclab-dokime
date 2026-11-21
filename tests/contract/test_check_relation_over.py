# SDD-EARS: CONTRACT-099 CONTRACT-100 CONTRACT-101
import pytest

from tests.contract.contracts import codes, line_of, only
from tests.contract.test_check_relations import CLI, FUNCTION, RELATION, relation, with_relation


def test_idempotent_at_a_function_of_two_arguments_needs_over() -> None:
    result = with_relation(relation(relation="idempotent", target=FUNCTION))
    only(result, "relation-needs-over")


def test_idempotent_at_a_function_of_one_argument_needs_no_over() -> None:
    text = relation("keep-empty-invoices", relation="idempotent", target=FUNCTION)
    assert codes(with_relation(text)) == []


@pytest.mark.parametrize("over", ["args[0]", "currency"])
def test_over_at_a_function_names_an_argument_that_an_example_gives(over: str) -> None:
    result = with_relation(relation(relation="idempotent", target=FUNCTION, over=over))
    assert codes(result) == []


@pytest.mark.parametrize("over", ["lines", "args[1]", "args[-1]", "args[x]", "two words"])
def test_over_at_a_function_that_names_no_argument_is_refused(over: str) -> None:
    result = with_relation(relation(relation="order-insensitive", target=FUNCTION, over=over))
    assert only(result, "bad-over").lines == (line_of(RELATION),)


@pytest.mark.parametrize("over", ["stdin", "invoice.json"])
def test_over_at_cli_is_stdin_or_a_file_of_the_input(over: str) -> None:
    result = with_relation(relation(relation="order-insensitive", target=CLI, over=over))
    assert codes(result) == []


@pytest.mark.parametrize(
    "fields",
    [
        {"relation": "order-insensitive", "target": CLI, "over": "other.json"},
        {"relation": "idempotent", "target": CLI, "via": "stdout", "over": "stdin"},
    ],
)
def test_over_at_cli_that_names_no_input_or_on_idempotent_is_refused(
    fields: dict[str, str],
) -> None:
    only(with_relation(relation(**fields)), "bad-over")
