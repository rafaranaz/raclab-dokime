# SDD-EARS: VERIFY-153 VERIFY-168
import dataclasses
import random

from dokime.contract.model import Contract
from dokime.core.verdicts import Verdict
from dokime.oracle.holdout import split as split_examples
from dokime.verify.sealed import Unheld, unheld_cases
from tests.verify.gates import codes
from tests.verify.sealed_contracts import UNHELD, batch_of, held, run, split

PAIR = (("E-h1", held("E-h1")), ("E-h2", held("E-h2")))


def full(contract: Contract, batch_texts: dict[str, str]) -> Contract:
    """The contract before the split: its visible examples and the held-out ones, in order."""
    from dokime.contract.check import check

    whole = check(
        'format: 1\nstory: S-1\nrequirements:\n  - {id: R-new, kind: new, text: "When the'
        ' function is called with a number, the function shall return two.", source: written}\n'
        "examples:\n" + "".join(batch_texts.values())
    )
    assert whole.contract is not None
    return dataclasses.replace(contract, examples=whole.contract.examples, held_out=())


def test_each_case_without_a_held_out_example_has_its_reason() -> None:
    contract, sealed = split(*PAIR)
    batch = batch_of(contract, sealed)
    texts = {e.id: e.text for e in sealed}
    from tests.verify.sealed_contracts import partner

    for n in range(2):
        texts[partner(n)] = held(partner(n), case=f"c{n}")
    texts["E-s1"] = held("E-s1", case="c-single")
    texts["E-q1"] = held("E-q1", case="c-pub")
    texts["E-q2"] = held("E-q2", case="c-pub")
    ordered = {i: texts[i] for i in batch.order}
    before = full(contract, ordered)
    done = split_examples(before, batch.seed, batch.kept_visible)
    assert unheld_cases(before, done) == UNHELD
    assert (
        Unheld("R-new", "c-single", "single-example"),
        Unheld("R-new", "c-pub", "all-published"),
    ) == UNHELD


def test_the_batch_as_sealed_passes_the_check_of_its_split() -> None:
    contract, sealed = split(*PAIR)
    result, observer = run(contract, batch_of(contract, sealed), {"E-h1": 2, "E-h2": 2})
    assert result.findings == ()
    assert observer.calls


def mismatch(contract: Contract, batch: object) -> None:
    result, observer = run(contract, batch, {"E-h1": 2, "E-h2": 2})  # type: ignore[arg-type]
    assert codes(list(result.findings)) == [("sealed-batch-mismatch", Verdict.ERROR)]
    assert observer.calls == []


def test_examples_kept_visible_that_draw_another_split_are_a_mismatch() -> None:
    contract, sealed = split(*PAIR)
    seed = next(
        s
        for s in range(1000)
        if random.Random(s).choice(["E-p0", "E-h1"]) == "E-p0"  # noqa: S311 - a draw to find
    )
    batch = batch_of(contract, sealed, seed=seed)
    mismatch(contract, dataclasses.replace(batch, kept_visible=("E-p1", "E-q1", "E-q2")))


def test_examples_kept_visible_that_the_contract_does_not_have_are_a_mismatch() -> None:
    contract, sealed = split(*PAIR)
    batch = batch_of(contract, sealed)
    mismatch(contract, dataclasses.replace(batch, kept_visible=(*batch.kept_visible, "E-zz")))


def test_another_reason_of_a_case_without_a_held_out_example_is_a_mismatch() -> None:
    contract, sealed = split(*PAIR)
    batch = batch_of(contract, sealed)
    swapped = tuple(dataclasses.replace(u, reason="single-example") for u in batch.unheld)
    mismatch(contract, dataclasses.replace(batch, unheld=swapped))


def test_a_case_without_a_held_out_example_left_out_is_a_mismatch() -> None:
    contract, sealed = split(*PAIR)
    batch = batch_of(contract, sealed)
    mismatch(contract, dataclasses.replace(batch, unheld=batch.unheld[:1]))


def test_an_order_without_every_example_is_a_mismatch() -> None:
    contract, sealed = split(*PAIR)
    batch = batch_of(contract, sealed)
    mismatch(contract, dataclasses.replace(batch, order=batch.order[:-1]))
