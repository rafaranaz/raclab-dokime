# SDD-EARS: EVIDENCE-020 EVIDENCE-021 EVIDENCE-022 EVIDENCE-023 EVIDENCE-024 EVIDENCE-025
import hashlib
import json

from dokime.core.ledger import Head
from dokime.core.policy import Policy
from dokime.core.verdicts import Verdict
from dokime.evidence.run import Image
from dokime.evidence.statement import build
from tests.evidence.runs import IMAGE, PLATFORM, inputs, predicate, run


def sha256(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def test_the_predicate_records_the_verdict_given_and_who_verified() -> None:
    given = predicate(run(verdict=Verdict.ASK, harness="1.2.3"))
    assert given["verdict"] == "ASK"
    assert given["delivered"] is False
    assert given["independence"] == "self-attested"
    assert given["verifier"] == {"harness": "1.2.3", "ran_on": "developer"}


def test_the_contract_is_recorded_by_the_digest_of_its_bytes() -> None:
    assert predicate()["contract"] == {"story": "S-1", "digest": sha256(b"story: S-1\n")}


def test_a_contract_that_was_not_read_leaves_only_its_story() -> None:
    assert predicate(run(contract=None))["contract"] == {"story": "S-1"}


def test_the_inputs_record_the_base_and_the_effective_policy() -> None:
    given = predicate()["inputs"]
    assert given["base"] == "2" * 40
    assert given["policy"] == {"digest": Policy().digest(), "source": "defaults"}
    from_file = Policy(baseline_runs=3, from_file=True)
    on_file = predicate(run(inputs=inputs(policy=from_file)))["inputs"]["policy"]
    assert on_file == {"digest": from_file.digest(), "source": "file"}


def test_the_inputs_reached_are_recorded() -> None:
    given = predicate()["inputs"]
    assert given["image"] == {"digest": IMAGE.text, "platform": PLATFORM.text}
    assert given["pack"] == {"digest": sha256(b"name: p\n")}
    assert given["probe"] == "sha256:" + "c" * 64


def test_an_image_from_scratch_has_no_platform() -> None:
    given = predicate(run(inputs=inputs(image=Image(IMAGE))))
    assert given["inputs"]["image"] == {"digest": IMAGE.text}


def test_the_inputs_not_reached_are_left_out() -> None:
    given = predicate(run(inputs=inputs(image=None, pack=None, probe=None)))
    assert set(given["inputs"]) == {"base", "policy"}


def test_no_human_decision_and_the_head_of_the_ledger() -> None:
    given = predicate()
    assert given["human_decisions"] == []
    assert given["ledger"] == {"head": "sha256:" + "d" * 64, "events": 7}


def test_an_empty_ledger_has_no_head() -> None:
    assert predicate(run(ledger=Head(hash=None, events=0)))["ledger"] == {"events": 0}


def test_the_predicate_has_only_the_fields_of_a3_and_never_null() -> None:
    given = predicate()
    assert set(given) == {
        "verdict",
        "delivered",
        "independence",
        "verifier",
        "contract",
        "inputs",
        "gates",
        "human_decisions",
        "not_checked",
        "ledger",
    }
    bare = run(contract=None, inputs=inputs(image=None, pack=None, probe=None))
    assert b"null" not in build(bare).data
    assert "null" not in json.dumps(predicate(bare))
