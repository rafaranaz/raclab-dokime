# SDD-EARS: VERIFY-045 VERIFY-046
from dokime.verify.result import Checks
from tests.verify.doubles import patch
from tests.verify.gates import contract, example, run_baseline, run_change

MIXED = contract(
    example("E-1", "R-new", "human"),
    example("E-2", "R-new", "model"),
    example("E-3", "R-keep", "derived"),
    example("E-4", "R-keep", "human"),
)
COUNTED = (Checks("human", 2), Checks("derived", 1), Checks("model", 1))


def test_baseline_counts_the_examples_of_the_contract_by_origin() -> None:
    result, _ = run_baseline(MIXED, {"E-1": 2, "E-2": 2, "E-3": 2, "E-4": 2}, runs=2)
    assert result.checks == COUNTED


def test_visible_examples_counts_the_examples_of_the_contract_by_origin() -> None:
    result, _ = run_change(MIXED, {"E-1": 5})
    assert result.checks == COUNTED


def test_a_refusal_gives_no_checks() -> None:
    on_base, _ = run_baseline(MIXED, {}, missing_base=True)
    on_change, _ = run_change(MIXED, {}, changed=patch(removes=["absent.py"]))
    assert [r.findings[0].code for r in (on_base, on_change)] == [
        "commit-missing",
        "patch-does-not-apply",
    ]
    assert (on_base.checks, on_change.checks) == ((), ())


def test_a_contract_without_examples_gives_no_checks() -> None:
    assert run_baseline(contract(), {})[0].checks == ()
    assert run_change(contract(), {})[0].checks == ()
