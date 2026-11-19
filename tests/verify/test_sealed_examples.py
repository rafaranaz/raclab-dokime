# SDD-EARS: VERIFY-160 VERIFY-161 VERIFY-162 VERIFY-163 VERIFY-164 VERIFY-165 VERIFY-166 VERIFY-167
import dataclasses

from dokime.core.verdicts import Verdict
from dokime.verify.result import Checks
from dokime.verify.sealed import NOT_HERE, SEALED, SealedExample
from tests.verify.gates import codes
from tests.verify.sealed_contracts import IMPOSSIBLE, batch_of, held, run, split

PAIR = (("E-h1", held("E-h1")), ("E-h2", held("E-h2")))


def test_held_out_examples_that_hold_and_a_canary_that_does_not_pass() -> None:
    contract, sealed = split(*PAIR)
    result, observer = run(contract, batch_of(contract, sealed), {"E-h1": 2, "E-h2": 2})
    assert result.gate == SEALED
    assert result.findings == ()
    assert result.checks == (Checks("human", 2),)
    ((_, requests),) = observer.calls
    assert sorted(r.example for r in requests) == ["E-cana", "E-h1", "E-h2"]


def test_a_held_out_example_that_fails_gives_the_words_of_the_oracle() -> None:
    contract, sealed = split(*PAIR)
    result, _ = run(contract, batch_of(contract, sealed), {"E-h1": 2, "E-h2": 5})
    (found,) = result.findings
    assert codes([found]) == [("sealed-example-fails", Verdict.FAIL)]
    assert found.message == "the requirement R-new fails a held-out example: returns"


def test_a_held_out_example_of_a_model_asks() -> None:
    contract, sealed = split(("E-h1", held("E-h1", origin="model")), ("E-h2", held("E-h2")))
    result, _ = run(contract, batch_of(contract, sealed), {"E-h1": 5, "E-h2": 2})
    assert codes(list(result.findings)) == [("sealed-model-example-fails", Verdict.ASK)]


def test_a_canary_that_holds_is_an_error_of_its_own() -> None:
    contract, sealed = split(*PAIR)
    result, _ = run(
        contract, batch_of(contract, sealed), {"E-h1": 2, "E-h2": 2, "E-cana": IMPOSSIBLE}
    )
    (found,) = result.findings
    assert codes([found]) == [("canary-passed", Verdict.ERROR)]


def test_no_finding_holds_a_value_an_input_or_an_identifier() -> None:
    contract, sealed = split(*PAIR)
    result, _ = run(
        contract, batch_of(contract, sealed), {"E-h1": 99, "E-h2": 98, "E-cana": IMPOSSIBLE}
    )
    assert len(result.findings) == 3
    for finding in result.findings:
        for leak in ("E-h1", "E-h2", "E-cana", "99", "98", IMPOSSIBLE, "args"):
            assert leak not in finding.message, (leak, finding.message)


def test_a_batch_with_another_text_is_a_mismatch_and_observes_nothing() -> None:
    contract, sealed = split(*PAIR)
    changed = (
        dataclasses.replace(sealed[0], text=sealed[0].text.replace("returns: 2", "returns: 3")),
        sealed[1],
    )
    result, observer = run(contract, batch_of(contract, changed), {"E-h1": 2, "E-h2": 2})
    assert codes(list(result.findings)) == [("sealed-batch-mismatch", Verdict.ERROR)]
    assert observer.calls == []


def test_a_batch_with_another_salt_is_a_mismatch() -> None:
    contract, sealed = split(*PAIR)
    changed = (dataclasses.replace(sealed[0], salt=bytes([9]) * 16), sealed[1])
    result, observer = run(contract, batch_of(contract, changed), {})
    assert codes(list(result.findings)) == [("sealed-batch-mismatch", Verdict.ERROR)]
    assert observer.calls == []


def test_a_batch_without_every_held_out_example_is_a_mismatch() -> None:
    contract, sealed = split(*PAIR)
    result, observer = run(contract, batch_of(contract, sealed[:1]), {})
    assert codes(list(result.findings)) == [("sealed-batch-mismatch", Verdict.ERROR)]
    assert observer.calls == []


def test_a_batch_with_an_example_the_contract_does_not_hold_out_is_a_mismatch() -> None:
    contract, sealed = split(*PAIR)
    extra = (*sealed, SealedExample("E-h9", bytes(16), held("E-h9")))
    result, observer = run(contract, batch_of(contract, extra), {})
    assert codes(list(result.findings)) == [("sealed-batch-mismatch", Verdict.ERROR)]
    assert observer.calls == []


def test_a_text_whose_id_is_not_its_own_is_a_mismatch() -> None:
    contract, sealed = split(("E-h1", held("E-h2")), ("E-h2", held("E-h2")))
    result, observer = run(contract, batch_of(contract, sealed), {})
    assert codes(list(result.findings)) == [("sealed-batch-mismatch", Verdict.ERROR)]
    assert observer.calls == []


def test_the_reason_where_the_key_is_not() -> None:
    assert NOT_HERE == "the key is not here"


def test_a_held_out_text_that_is_not_an_example_is_a_mismatch() -> None:
    contract, sealed = split(("E-h1", "  - id: E-h1\n    steps: [\n"), ("E-h2", held("E-h2")))
    result, observer = run(contract, batch_of(contract, sealed), {})
    assert codes(list(result.findings)) == [("sealed-batch-mismatch", Verdict.ERROR)]
    assert observer.calls == []


def test_a_refusal_of_the_port_that_observes_is_an_error() -> None:
    from dokime.core.repository import RefusalError
    from tests.verify.sealed_contracts import run_with

    contract, sealed = split(*PAIR)
    refusal = RefusalError("observation-failed", "it died")
    result = run_with(contract, batch_of(contract, sealed), refusal)
    assert codes(list(result.findings)) == [("observation-failed", Verdict.ERROR)]
