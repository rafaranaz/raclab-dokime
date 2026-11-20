# SDD-EARS: VERIFY-175 VERIFY-176 VERIFY-177 VERIFY-178 VERIFY-167
import pytest

from dokime.core.verdicts import Verdict
from dokime.verify.result import GateResult
from dokime.verify.sealed import NOT_HERE, NOT_SEALED, SEALED, applicability
from tests.verify.gates import codes


def finding_of(result: object) -> list[tuple[str, Verdict]]:
    assert isinstance(result, GateResult)
    assert result.gate == SEALED
    return codes(list(result.findings))


@pytest.mark.parametrize("key", [True, False])
def test_a_batch_that_the_contract_does_not_name_is_a_mismatch_with_or_without_the_key(
    key: bool,
) -> None:
    result = applicability(holds_out=False, batched=True, key=key)
    assert finding_of(result) == [("sealed-batch-mismatch", Verdict.ERROR)]


@pytest.mark.parametrize("key", [True, False])
def test_held_out_examples_without_their_batch_are_missing_with_or_without_the_key(
    key: bool,
) -> None:
    result = applicability(holds_out=True, batched=False, key=key)
    assert finding_of(result) == [("sealed-batch-missing", Verdict.ERROR)]


@pytest.mark.parametrize("key", [True, False])
def test_a_contract_never_sealed_is_not_applicable_with_a_reason_of_its_own(key: bool) -> None:
    assert applicability(holds_out=False, batched=False, key=key) == NOT_SEALED
    assert NOT_SEALED == "the contract holds out no example"
    assert NOT_SEALED != NOT_HERE


def test_a_sealed_contract_without_the_key_is_not_applicable_as_the_key_is_not_here() -> None:
    assert applicability(holds_out=True, batched=True, key=False) == NOT_HERE


def test_a_sealed_contract_with_the_key_runs() -> None:
    assert applicability(holds_out=True, batched=True, key=True) is None
