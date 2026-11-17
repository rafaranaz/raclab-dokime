# SDD-EARS: EVIDENCE-083 EVIDENCE-084
import copy
from typing import Any

import pytest

from dokime.core.canonical import canonical
from dokime.core.verdicts import Verdict
from dokime.evidence.schema import read_back
from tests.evidence.runs import statement

GONE = object()
"""A field taken out of the statement."""


def changed(*changes: tuple[str, object]) -> list[tuple[str, str]]:
    """The findings of the statement of the whole run with each place given changed."""
    value = copy.deepcopy(statement())
    for place, new in changes:
        *path, last = [int(part) if part.isdigit() else part for part in place.split("/")]
        parent: Any = value
        for part in path:
            parent = parent[part]
        if new is GONE:
            del parent[last]
        else:
            parent[last] = new
    found = read_back(canonical(value).encode())
    assert all(f.verdict is Verdict.ERROR for f in found)
    return [(f.code, f.message) for f in found]


@pytest.mark.parametrize(
    ("place", "new"),
    [
        ("extra", 1),
        ("subject", "x"),
        ("predicate/verifier", "x"),
        ("predicate/gates", "x"),
        ("predicate/gates/1/findings", "x"),
        ("_type", "https://in-toto.io/Statement/v0.1"),
        ("predicateType", "https://example.org/other"),
        ("subject/0/digest/gitTree", "XYZ"),
        ("subject/1/name", "other.patch"),
        ("subject/1", GONE),
        ("predicate/verdict", "MAYBE"),
        ("predicate/verdict", None),
        ("predicate/delivered", True),
        ("predicate/independence", "ci-verified"),
        ("predicate/verifier/ran_on", "ci"),
        ("predicate/verifier/harness", 1),
        ("predicate/author", {}),
        ("predicate/contract/approval", "sha256:" + "e" * 64),
        ("predicate/contract/story", "a/b"),
        ("predicate/contract/digest", "md5:00"),
        ("predicate/inputs/base", "abc"),
        ("predicate/inputs/policy/source", "environment"),
        ("predicate/inputs/image/platform", None),
        ("predicate/inputs/pack/level", "P2"),
        ("predicate/inputs/probe", "sha256:short"),
        ("predicate/gates/0/status", "skipped"),
        ("predicate/gates/1/findings/0/verdict", "PASS"),
        ("predicate/gates/1/findings/0/code", "Not A Code"),
        ("predicate/gates/1/findings/0/lines", [0]),
        ("predicate/gates/1/findings/0/untrusted", []),
        ("predicate/gates/1/findings/0/untrusted/0/label", "observed"),
        ("predicate/gates/1/checks/0/origin", "sealed"),
        ("predicate/gates/1/checks/0/total", 0),
        ("predicate/gates/1/checks", []),
        ("predicate/gates/4/reason", GONE),
        ("predicate/human_decisions", [{}]),
        ("predicate/not_checked/0/code", "made-up"),
        ("predicate/not_checked/0/what", "a b"),
        ("predicate/not_checked/5/untrusted/0/text", 3),
        ("predicate/not_checked", GONE),
        ("predicate/ledger/events", -1),
        ("predicate/ledger/events", True),
        ("predicate/ledger/head", "sha256:" + "z" * 64),
    ],
)
def test_a_statement_out_of_the_schema_is_refused_where_it_breaks(place: str, new: object) -> None:
    ((code, message),) = changed((place, new))
    assert code == "evidence-schema"
    assert place in message


def test_a_third_subject_is_refused() -> None:
    subjects = statement()["subject"]
    ((code, message),) = changed(("subject", [*subjects, subjects[0]]))
    assert code == "evidence-schema"
    assert "subject/2" in message


def test_a_repeated_gate_is_refused() -> None:
    gates = statement()["predicate"]["gates"]
    ((code, message),) = changed(("predicate/gates", [*gates, gates[0]]))
    assert code == "evidence-schema"
    assert "predicate/gates" in message
    assert "contract" in message


def test_every_place_that_breaks_is_reported_in_the_order_of_the_statement() -> None:
    found = changed(
        ("predicate/ledger/events", -1),
        ("subject/0/digest/gitTree", "XYZ"),
        ("predicate/verdict", "MAYBE"),
    )
    places = [message for _, message in found]
    assert len(places) == 3
    assert "subject/0/digest/gitTree" in places[0]
    assert "predicate/verdict" in places[1]
    assert "predicate/ledger/events" in places[2]
