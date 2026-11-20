# SDD-EARS: EVIDENCE-048 EVIDENCE-060 EVIDENCE-066 EVIDENCE-069 EVIDENCE-070
from typing import Any

from tests.evidence.runs import BATCH, predicate, run, sealed

LIMITS = [
    "the content of an example is compared as YAML reads it, so one published with a field added or"
    " a value spelt otherwise is not recognised",
    "a version of the contract under an earlier path, after a rename, is not read",
    "a commit that only other refs reach is not read",
    "a copy of an example in another file is not looked for",
    "the history is read up to the base of the pull request, so a held-out example published in a"
    " commit of the pull request and taken back in another is not seen by this audit: where the"
    " project merges keeping the commits, by rebase or by a merge commit, the next audit sees it,"
    " and with a squash merge no audit does",
]


def sealed_entry(given: dict[str, Any]) -> dict[str, Any]:
    (entry,) = [g for g in given["gates"] if g["gate"] == "sealed-examples"]
    found: dict[str, Any] = entry
    return found


def test_the_gate_that_observed_records_its_hold_out_in_the_order_given() -> None:
    assert sealed_entry(predicate(sealed()))["holdout"] == {
        "batch": BATCH,
        "held": [{"requirement": "R-1", "case": "c1"}, {"requirement": "R-3", "case": "c3"}],
        "kept_visible": ["E-k1", "E-k2"],
        "without_holdout": [
            {"requirement": "R-1", "case": "c-single", "motive": "single-example"},
            {"requirement": "R-3", "case": "c-pub", "motive": "all-published"},
        ],
    }


def test_each_case_without_a_held_out_example_is_not_checked_with_its_motive() -> None:
    listed = [e for e in predicate(sealed())["not_checked"] if e["code"] == "case-without-holdout"]
    assert listed == [
        {
            "code": "case-without-holdout",
            "what": "R-1",
            "case": "c-single",
            "reason": "the case has a single example",
        },
        {
            "code": "case-without-holdout",
            "what": "R-3",
            "case": "c-pub",
            "reason": "every example of the case was published before the seal",
        },
    ]


def test_each_limit_of_the_detection_is_not_checked_in_the_order_of_the_adr() -> None:
    listed = [e for e in predicate(sealed())["not_checked"] if e["code"] == "best-effort-secrecy"]
    assert [e["what"] for e in listed] == ["sealed-examples"] * 5
    assert [e["reason"] for e in listed] == LIMITS


def test_the_codes_of_a_sealed_run_come_in_their_order() -> None:
    codes = list(dict.fromkeys(e["code"] for e in predicate(sealed())["not_checked"]))
    assert codes == [
        "case-without-holdout",
        "requirement-without-example",
        "only-model-checks",
        "test-excluded-unstable",
        "example-unstable",
        "outside-threat-model",
        "best-effort-secrecy",
    ]


def test_no_holdout_is_written_no_more() -> None:
    for given in (run(), sealed()):
        assert all(e["code"] != "no-holdout" for e in predicate(given)["not_checked"])


def test_without_a_hold_out_nothing_of_it_is_written() -> None:
    for given in (run(), sealed(holdout=None)):
        value = predicate(given)
        assert "holdout" not in sealed_entry(value)
        codes = {e["code"] for e in value["not_checked"]}
        assert codes.isdisjoint({"case-without-holdout", "best-effort-secrecy"})
