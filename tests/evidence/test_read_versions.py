# SDD-EARS: EVIDENCE-090 EVIDENCE-091
import copy
from typing import Any

import pytest

from dokime.core.canonical import canonical
from dokime.core.repository import CommitName
from dokime.evidence.run import Repeated
from dokime.evidence.schema import read_back
from tests.evidence.runs import changed, run, statement

V01 = "https://github.com/rafaranaz/raclab-dokime/attestation/conformance/v0.1"


def as_v01(value: dict[str, Any]) -> list[tuple[str, str]]:
    old = copy.deepcopy(value)
    old["predicateType"] = V01
    return [(f.code, f.message) for f in read_back(canonical(old).encode())]


def test_a_file_of_v01_is_read_with_the_schema_of_v01() -> None:
    assert as_v01(statement()) == []


@pytest.mark.parametrize(
    ("given", "place"),
    [
        (run(harness_commit=CommitName("e" * 40)), "predicate/verifier/commit"),
        (run(repeated=Repeated(runs=2, consistent=True)), "predicate/repeated"),
    ],
)
def test_a_field_of_v02_in_a_file_of_v01_is_refused(given: Any, place: str) -> None:
    ((code, message),) = as_v01(statement(given))
    assert code == "evidence-schema"
    assert place in message


def test_a_finding_of_v01_has_no_message() -> None:
    value = statement()
    value["predicate"]["gates"][5]["findings"][0]["message"] = "the example fails"
    ((_code, message),) = as_v01(value)
    assert "predicate/gates/5/findings/0/message" in message


def test_a_finding_of_v02_may_carry_a_trusted_message() -> None:
    place = "predicate/gates/5/findings/0/message"
    assert changed((place, "the example fails")) == []
    assert changed((place, "m" * 4096)) == []
    for wrong in ("", "m" * 4097, 3):
        ((_code, message),) = changed((place, wrong))
        assert place in message


@pytest.mark.parametrize(
    ("place", "new"),
    [
        ("predicate/repeated", {"runs": 1, "consistent": True}),
        ("predicate/repeated", {"runs": 2, "consistent": "yes"}),
        ("predicate/verifier/commit", "HEAD"),
        ("predicate/inputs/change_image", {"digest": "sha256:short"}),
    ],
)
def test_the_fields_of_v02_are_checked(place: str, new: object) -> None:
    ((code, message),) = changed((place, new))
    assert code == "evidence-schema"
    assert place in message
