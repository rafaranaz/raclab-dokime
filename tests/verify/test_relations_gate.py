# SDD-EARS: VERIFY-179 VERIFY-180 VERIFY-181 VERIFY-182 VERIFY-187
from collections.abc import Mapping

from dokime.contract.check import check
from dokime.core.observation import StepObservation
from dokime.verify.relations import GATE, source_seed
from tests.verify.relation_runs import (
    EXAMPLES,
    HEADER,
    LINES,
    ONCE,
    ORDER,
    ComputingObserver,
    contract,
    run,
    sorting,
)


def requested(observer: ComputingObserver) -> list[list[str]]:
    return [[request.example for request in call] for call in observer.calls]


def test_the_sources_are_the_visible_examples_of_one_step_of_the_requirement_and_target() -> None:
    observer = ComputingObserver(sorting)
    outcome = run(contract(ORDER), observer)
    assert outcome.result.gate == GATE
    assert outcome.result.findings == ()
    (sources, follow_ups) = requested(observer)
    assert sources == ["E-1", "E-2"]
    assert all(name.split("/")[1] in {"E-1", "E-2"} for name in follow_ups)


def test_a_held_out_example_is_never_a_source() -> None:
    stub = "held_out:\n  - id: E-9\n    requirement: R-sort\n    case: c-9\n"
    stub += "    digest: sha256:" + "0" * 64 + "\n"
    checked = check(HEADER + "examples:\n" + EXAMPLES + stub + "relations:\n" + ORDER)
    assert checked.contract is not None, checked.findings
    observer = ComputingObserver(sorting)
    run(checked.contract, observer)
    assert all("E-9" not in name for call in requested(observer) for name in call)


def test_the_follow_ups_are_observed_after_their_sources_with_the_inputs_built() -> None:
    observer = ComputingObserver(sorting)
    run(contract(ORDER), observer, permutations=1)
    (_, follow_ups) = observer.calls
    by_source: dict[str, list[object]] = {}
    for request in follow_ups:
        by_source.setdefault(request.example.split("/")[1], []).append(request.inputs[0]["args"])
    assert by_source["E-1"][0] == [[2, 1, 3]]
    assert len(by_source["E-1"]) == 2
    assert [[3, 1, 2]] not in by_source["E-1"]
    assert by_source["E-2"] == [[[4, 5]]]


def test_order_insensitive_over_a_file_keeps_the_relation_for_a_program_that_only_prints() -> None:
    outcome = run(contract(LINES), ComputingObserver(sorting))
    assert outcome.result.findings == ()
    assert outcome.failed == ()


def test_the_same_seed_gives_the_same_follow_ups() -> None:
    first, second = ComputingObserver(sorting), ComputingObserver(sorting)
    run(contract(ORDER), first, seed=7, permutations=3)
    run(contract(ORDER), second, seed=7, permutations=3)
    assert first.calls == second.calls
    assert source_seed(7, "L1", "E-1") == source_seed(7, "L1", "E-1")
    assert source_seed(7, "L1", "E-1") != source_seed(7, "L1", "E-2")
    assert source_seed(7, "L1", "E-1") != source_seed(7, "L2", "E-1")
    assert source_seed(7, "L1", "E-1") != source_seed(8, "L1", "E-1")


def test_a_source_not_observed_to_its_end_has_no_follow_up() -> None:
    def stalls(target: str, given: Mapping[str, object]) -> StepObservation | None:
        return None if given["args"] == [[3, 1, 2]] else sorting(target, given)

    observer = ComputingObserver(stalls)
    run(contract(ORDER), observer)
    (_, follow_ups) = observer.calls
    assert {r.example.split("/")[1] for r in follow_ups} == {"E-2"}


def test_a_follow_up_not_observed_to_its_end_does_not_hold() -> None:
    def stalls(target: str, given: Mapping[str, object]) -> StepObservation | None:
        return None if given["args"] == [[4, 5]] else sorting(target, given)

    outcome = run(contract(ORDER), ComputingObserver(stalls))
    assert [f.code for f in outcome.result.findings] == ["relation-fails"]
    assert [(f.relation, f.example) for f in outcome.failed] == [("L1", "E-2")]


def test_idempotent_runs_again_on_the_return() -> None:
    observer = ComputingObserver(sorting)
    outcome = run(contract(ONCE), observer)
    assert outcome.result.findings == ()
    (_, follow_ups) = observer.calls
    assert [r.inputs[0]["args"] for r in follow_ups] == [[[1, 2, 3]], [[4, 5]]]
