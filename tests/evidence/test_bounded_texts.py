# SDD-EARS: EVIDENCE-047 EVIDENCE-068 EVIDENCE-089
from typing import Any

from dokime.core.findings import Finding
from dokime.core.verdicts import Verdict
from dokime.evidence.run import GateRan
from dokime.evidence.schema import read_back
from dokime.evidence.statement import build
from tests.evidence.runs import GATES, changed, gates_with, predicate, run


def with_message(text: str) -> dict[str, Any]:
    found = Finding(code="example-fails", message=text, verdict=Verdict.FAIL)
    gate = GateRan("visible-examples", Verdict.FAIL, findings=(found,))
    (written,) = predicate(run(gates=gates_with(gate)))["gates"][5]["findings"]
    value: dict[str, Any] = written["untrusted"][0]
    return value


def with_test(name: str) -> dict[str, Any]:
    gate = GateRan("existing-tests", Verdict.PASS, unstable_tests=(name,))
    entries = predicate(run(gates=gates_with(gate)))["not_checked"]
    (entry,) = [e for e in entries if e["code"] == "test-excluded-unstable"]
    value: dict[str, Any] = entry["untrusted"][0]
    return value


def test_a_message_longer_than_4096_characters_is_cut() -> None:
    long = "é" * 4000 + "x" * 1000
    assert with_message(long)["text"] == long[:4095] + "…"


def test_a_message_of_4096_characters_is_kept_whole() -> None:
    assert with_message("m" * 4096)["text"] == "m" * 4096


def test_a_test_name_longer_than_200_characters_is_cut() -> None:
    long = "tests.test_a::" + "t" * 300
    assert with_test(long)["text"] == long[:199] + "…"
    assert with_test("n" * 200)["text"] == "n" * 200


def test_a_run_with_long_texts_reads_back_without_a_finding() -> None:
    found = Finding(code="example-fails", message="x" * 9000, verdict=Verdict.FAIL)
    gates = gates_with(
        GateRan("visible-examples", Verdict.FAIL, findings=(found,)),
        GateRan("existing-tests", Verdict.PASS, unstable_tests=("t" * 900,)),
    )
    assert read_back(build(run(gates=gates)).data) == ()
    assert len(GATES) == 11


def test_a_message_longer_than_4096_characters_is_refused() -> None:
    place = "predicate/gates/5/findings/0/untrusted/0/text"
    ((code, message),) = changed((place, "m" * 4097))
    assert code == "evidence-schema"
    assert place in message


def test_a_quoted_text_longer_than_200_characters_is_refused() -> None:
    place = "predicate/not_checked/2/untrusted/0/text"
    ((code, message),) = changed((place, "t" * 201))
    assert code == "evidence-schema"
    assert place in message
    assert changed((place, "t" * 200)) == []
