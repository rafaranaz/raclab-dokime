# SDD-EARS: VERIFY-183 VERIFY-184 VERIFY-185 VERIFY-186
from collections.abc import Mapping

from dokime.core.observation import Returned, StepObservation
from dokime.core.repository import RefusalError
from dokime.core.verdicts import Verdict
from dokime.oracle.relations import words
from dokime.verify.result import Checks
from tests.verify.doubles import AuditedDouble
from tests.verify.relation_runs import (
    ONCE,
    ORDER,
    ComputingObserver,
    contract,
    example,
    raising,
    run,
    sorting,
)


def keeping(target: str, given: Mapping[str, object]) -> StepObservation:
    """A program that returns the list as it got it: idempotent, but not order-insensitive."""
    args = given["args"]
    assert isinstance(args, list)
    return Returned(list(args[0]))


def adding(target: str, given: Mapping[str, object]) -> StepObservation:
    """A program that adds one to each item and sorts them: not idempotent."""
    args = given["args"]
    assert isinstance(args, list)
    return Returned(sorted(item + 1 for item in args[0]))


def test_a_relation_without_a_follow_up_asks_at_its_line() -> None:
    of = contract(ONCE)
    outcome = run(of, ComputingObserver(raising))
    (finding,) = outcome.result.findings
    assert (finding.code, finding.verdict) == ("relation-without-source", Verdict.ASK)
    assert finding.lines == (of.relations[0].line,)


def test_a_relation_that_does_not_hold_fails_once_for_each_source() -> None:
    of = contract(ORDER)
    outcome = run(of, ComputingObserver(keeping), permutations=3)
    found = outcome.result.findings
    assert [(f.code, f.verdict) for f in found] == [("relation-fails", Verdict.FAIL)] * 2
    assert {f.message for f in found} == {
        words(of.relations[0], "E-1"),
        words(of.relations[0], "E-2"),
    }
    assert all(f.lines == (of.relations[0].line,) for f in found)


def test_idempotent_that_does_not_hold_fails() -> None:
    outcome = run(contract(ONCE), ComputingObserver(adding))
    assert [f.code for f in outcome.result.findings] == ["relation-fails", "relation-fails"]
    assert {(f.relation, f.example, f.order) for f in outcome.failed} == {
        ("L2", "E-1", None),
        ("L2", "E-2", None),
    }


def test_the_result_counts_the_follow_ups_and_gives_the_seed_and_the_orders_that_failed() -> None:
    outcome = run(contract(ORDER), ComputingObserver(keeping), seed=11, permutations=1)
    assert outcome.seed == 11
    assert outcome.result.checks == (Checks("derived", 3),)
    assert {f.example for f in outcome.failed} == {"E-1", "E-2"}
    assert all(f.relation == "L1" and f.order is not None for f in outcome.failed)
    assert ("L1", "E-2", (1, 0)) in {(f.relation, f.example, f.order) for f in outcome.failed}


def test_a_refusal_of_the_observer_is_an_error_and_nothing_else() -> None:
    refused = RefusalError("engine-failed", "podman failed")
    outcome = run(contract(ORDER), ComputingObserver(sorting, refusal=refused))
    assert [(f.code, f.verdict) for f in outcome.result.findings] == [
        ("engine-failed", Verdict.ERROR)
    ]
    assert outcome.result.checks == ()


def test_a_refusal_of_the_repository_is_an_error_and_nothing_else() -> None:
    class Refusing(AuditedDouble):
        def compose_with_patch(self, base, changed):  # type: ignore[no-untyped-def]
            raise RefusalError("patch-does-not-apply", "the patch does not apply")

    outcome = run(contract(ORDER), ComputingObserver(sorting), repository=Refusing())
    assert [f.code for f in outcome.result.findings] == ["patch-does-not-apply"]


def test_a_source_whose_input_named_by_over_is_not_a_list_has_no_follow_up() -> None:
    of = contract(ORDER, example("E-1", "R-sort", "p:sort", "{args: [text]}"))
    observer = ComputingObserver(raising)
    outcome = run(of, observer)
    assert [f.code for f in outcome.result.findings] == ["relation-without-source"]
    assert len(observer.calls) == 1
