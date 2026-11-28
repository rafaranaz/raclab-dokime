# SDD-EARS: CORPUS-120 CORPUS-121 CORPUS-122 CORPUS-123 CORPUS-126
"""The entry of the results that a run of R2 leaves, the only thing meant to leave the machine of
the maintainer: its fields, its counts and the strict xfail of mdformat."""

import tomllib
from dataclasses import fields
from pathlib import Path
from typing import Any

import pytest

from tests.corpus.contrast.runs import (
    XFAIL,
    Entry,
    entry_of,
    example_tests,
    failed_run,
    toml_of,
    witness_tests,
)

FIELDS = [
    "key",
    "arm",
    "state",
    "regression",
    "visible_passed",
    "visible_failed",
    "held_out_passed",
    "held_out_failed",
    "xfail_only",
    "failure",
    "without_strict_xfail",
]


def observed(name: str, after: str) -> dict[str, Any]:
    return {"id": name, "after": after, "base": "fail", "classification": "fixed"}


def visible(name: str) -> str:
    return f"tests.dokime_visible.test_dokime_examples::test_dokime_example[{name}]"


def held(name: str) -> str:
    return f"tests.dokime_held_out.test_dokime_examples::test_dokime_example[{name}]"


OBSERVATIONS = {
    "checks": [
        {"name": "test", "tests": [observed("tests.test_a::test_one", "pass")]},
        {
            "name": "dokime-visible",
            "tests": [
                observed("tests.dokime_visible.dokime.core.policy", "fail"),
                observed(visible("E-1"), "pass"),
                observed(visible("E-2"), "fail"),
                observed(visible("E-3"), "pass"),
                observed("tests.test_a::test_one", "pass"),
            ],
        },
    ],
    "sealed": [
        observed("tests.dokime_held_out.dokime.core.policy", "fail"),
        observed(held("h1"), "pass"),
        observed(held("h2"), "fail"),
        observed(held("h3"), "error"),
        observed("tests.test_a::test_one", "pass"),
    ],
}
RESULT = {"state": "incomplete", "regression": {"status": "found"}}
VISIBLE = example_tests("tests/dokime_visible", ["E-1", "E-2", "E-3"])
HELD = example_tests("tests/dokime_held_out", ["h1", "h2", "h3"])


def test_an_entry_holds_its_fields_and_nothing_else() -> None:
    entry = entry_of("p/c", "S2", RESULT, OBSERVATIONS, VISIBLE, HELD)
    read = tomllib.loads(toml_of(entry))
    assert [field.name for field in fields(Entry)] == FIELDS
    assert list(read) == ["run"]
    (run,) = read["run"]
    assert list(run) == FIELDS
    assert run["key"] == "p/c"
    assert run["arm"] == "S2"
    assert run["state"] == "incomplete"
    assert run["regression"] == "found"


def test_the_entries_of_several_runs_read_as_one_file() -> None:
    first = entry_of("p/c", "S0", RESULT, OBSERVATIONS, VISIBLE, HELD)
    second = failed_run("p/d", "S1", "mount")
    read = tomllib.loads(toml_of(first) + toml_of(second))
    assert [run["key"] for run in read["run"]] == ["p/c", "p/d"]


def test_no_id_of_a_test_reaches_the_entry() -> None:
    text = toml_of(entry_of("p/c", "S2", RESULT, OBSERVATIONS, VISIBLE, HELD))
    for name in ("h1", "h2", "E-1", "test_one", "dokime_held_out"):
        assert name not in text


def test_the_visible_tests_are_those_of_the_visible_conversion_in_its_check() -> None:
    entry = entry_of("p/c", "S2", RESULT, OBSERVATIONS, VISIBLE, HELD)
    assert (entry.visible_passed, entry.visible_failed) == (2, 1)


def test_in_s2_the_held_out_tests_are_those_of_the_sealed_conversion() -> None:
    entry = entry_of("p/c", "S2", RESULT, OBSERVATIONS, VISIBLE, HELD)
    assert (entry.held_out_passed, entry.held_out_failed) == (1, 2)


def test_in_s1_the_held_out_tests_are_those_the_witness_turned_green() -> None:
    observations = {
        "checks": [],
        "sealed": [
            observed("tests.test_a::test_green[1]", "pass"),
            observed("tests.test_a::test_green[2]", "fail"),
            observed("tests.test_a::test_other", "fail"),
        ],
    }
    witness = ["tests.test_a::test_green[1]", "tests.test_a::test_green[2]"]
    entry = entry_of("p/c", "S1", RESULT, observations, (), witness_tests(witness, {}))
    assert (entry.held_out_passed, entry.held_out_failed) == (1, 1)
    assert (entry.visible_passed, entry.visible_failed) == (0, 0)


def test_in_s1_the_witness_tests_are_counted_under_the_path_where_they_were_sealed() -> None:
    observations = {
        "checks": [],
        "sealed": [
            observed("tests.test_a_witness::test_green[1]", "pass"),
            observed("guide.u.x_witness.rst::x_witness.rst", "fail"),
            observed("tests.test_a::test_green[1]", "pass"),
        ],
    }
    witness = ["tests.test_a::test_green[1]", "guide.u.x.rst::x.rst"]
    moved = {"tests/test_a.py": "tests/test_a_witness.py", "guide/u/x.rst": "guide/u/x_witness.rst"}
    entry = entry_of("p/c", "S1", RESULT, observations, (), witness_tests(witness, moved))
    assert (entry.held_out_passed, entry.held_out_failed) == (1, 1)


def only(failing: list[str], state: str = "incomplete") -> bool:
    observations = {
        "checks": [
            {
                "name": "test",
                "tests": [observed(name, "fail") for name in failing]
                + [observed("tests.test_a::test_one", "pass")],
            }
        ],
        "sealed": [],
    }
    result = {"state": state, "regression": {"status": "found"}}
    return entry_of("mdformat/c", "S0", result, observations, (), ()).xfail_only


def test_a_rejection_from_the_strict_xfail_test_alone_is_recorded() -> None:
    assert only([XFAIL]) is True


def test_a_rejection_with_another_failing_test_is_not_from_the_xfail_alone() -> None:
    assert only([XFAIL, "tests.test_a::test_two"]) is False
    assert only(["tests.test_a::test_two"]) is False


def test_a_complete_run_is_no_rejection() -> None:
    assert only([XFAIL], state="complete") is False


def test_a_held_out_failure_besides_the_xfail_is_not_from_the_xfail_alone() -> None:
    observations = {
        "checks": [{"name": "test", "tests": [observed(XFAIL, "fail")]}],
        "sealed": [observed(held("h1"), "fail")],
    }
    result = {"state": "incomplete", "regression": {"status": "found"}}
    entry = entry_of("mdformat/c", "S2", result, observations, (), HELD)
    assert entry.xfail_only is False


def test_the_xfail_test_is_the_one_the_witness_turned_green() -> None:
    witnesses = tomllib.loads((Path(__file__).parent / "witnesses.toml").read_text())["witness"]
    of_the_fix = [w for w in witnesses if w.get("commit", "").startswith("27e2ba3")]
    assert of_the_fix
    assert all(witness["turned_green"] == [XFAIL] for witness in of_the_fix)


@pytest.mark.parametrize("kind", ["mount", "helper"])
def test_a_failure_is_recorded_by_its_kind_with_no_message(kind: str) -> None:
    entry = failed_run("p/c", "S1", kind)
    assert entry.failure == kind
    assert (entry.state, entry.regression) == ("", "")
    (run,) = tomllib.loads(toml_of(entry))["run"]
    assert list(run) == FIELDS


def test_a_failure_of_no_known_kind_is_refused() -> None:
    with pytest.raises(ValueError, match="no kind of failure"):
        failed_run("p/c", "S1", "the log of the run")


def test_a_witness_test_that_did_not_run_counts_as_failed() -> None:
    observations = {"checks": [], "sealed": [observed("tests.test_a::test_green[1]", "pass")]}
    witness = ["tests.test_a::test_green[1]", "tests.test_a::test_green[2]"]
    entry = entry_of("p/c", "S1", RESULT, observations, (), witness_tests(witness, {}))
    assert (entry.held_out_passed, entry.held_out_failed) == (1, 1)


def test_a_visible_example_that_did_not_run_counts_as_failed() -> None:
    observations = {
        "checks": [{"name": "dokime-visible", "tests": [observed(visible("E-1"), "pass")]}],
        "sealed": [],
    }
    entry = entry_of("p/c", "S2", RESULT, observations, VISIBLE, ())
    assert (entry.visible_passed, entry.visible_failed) == (1, 2)


def test_a_held_out_example_that_did_not_run_counts_as_failed() -> None:
    observations = {"checks": [], "sealed": [observed(held("h1"), "pass")]}
    entry = entry_of("p/c", "S2", RESULT, observations, (), HELD)
    assert (entry.held_out_passed, entry.held_out_failed) == (1, 2)


def test_a_test_that_is_not_expected_is_not_counted() -> None:
    observations = {
        "checks": [{"name": "dokime-visible", "tests": [observed(visible("E-9"), "fail")]}],
        "sealed": [observed(held("h9"), "fail")],
    }
    entry = entry_of("p/c", "S2", RESULT, observations, (), ())
    assert (entry.visible_failed, entry.held_out_failed) == (0, 0)


def test_an_entry_is_of_the_default_run_unless_the_command_says_otherwise() -> None:
    entries = [
        entry_of("p/c", "S0", RESULT, OBSERVATIONS, (), ()),
        failed_run("p/c", "S1", "mount"),
    ]
    for entry in entries:
        (run,) = tomllib.loads(toml_of(entry))["run"]
        assert run["without_strict_xfail"] is False
