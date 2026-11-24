# SDD-EARS: BENCH-013 BENCH-014 BENCH-015 BENCH-016 BENCH-017
import json
from pathlib import Path

import pytest

from dokime.bench.__main__ import main
from dokime.bench.corpus import read_corpus
from dokime.bench.metrics import Count, changes, hold_out, withdrawals
from dokime.bench.results import BenchError, read_run
from tests.bench.corpora import RUNNABLE, write_corpus, write_results


def test_each_withdrawn_case_is_listed_with_its_first_run(tmp_path: Path) -> None:
    listed = {w.key: w for w in withdrawals(read_corpus(write_corpus(tmp_path / "corpus")))}
    assert set(listed) == {"p/good-gone", "p/bad-gone"}
    assert (listed["p/good-gone"].verdict, listed["p/good-gone"].failing_gate) == (
        "FAIL",
        "protected-paths",
    )
    assert (listed["p/bad-gone"].verdict, listed["p/bad-gone"].failing_gate) == ("PASS", None)


def test_a_withdrawn_good_case_that_failed_is_a_false_reject_caused_by_its_contract(
    tmp_path: Path,
) -> None:
    listed = {w.key: w for w in withdrawals(read_corpus(write_corpus(tmp_path / "corpus")))}
    assert listed["p/good-gone"].false_reject_caused_by_its_contract
    assert not listed["p/bad-gone"].false_reject_caused_by_its_contract


def test_the_value_of_the_hold_out_gives_the_run_without_the_key_and_the_last_with_it(
    tmp_path: Path,
) -> None:
    corpus = read_corpus(write_corpus(tmp_path / "corpus"))
    held = hold_out(corpus, read_run(write_results(tmp_path / "r.jsonl", RUNNABLE)))
    assert held.without_the_key == Count(1, 1, False)
    assert held.with_the_key == Count(0, 1, True)
    assert held.not_run_with_the_key == ()


def test_two_runs_of_one_commit_give_the_cases_that_changed(tmp_path: Path) -> None:
    first = read_run(write_results(tmp_path / "1.jsonl", RUNNABLE))
    second = read_run(write_results(tmp_path / "2.jsonl", {**RUNNABLE, "p/good-two": "PASS"}))
    assert changes(first, second) == ["p/good-two"]
    assert changes(first, first) == []


def test_two_runs_of_different_commits_are_refused_giving_both(tmp_path: Path) -> None:
    first = read_run(write_results(tmp_path / "1.jsonl", RUNNABLE))
    second = read_run(write_results(tmp_path / "2.jsonl", RUNNABLE, commit="b" * 40))
    with pytest.raises(BenchError) as refused:
        changes(first, second)
    assert first.commit in str(refused.value)
    assert second.commit in str(refused.value)


def test_the_command_writes_the_metrics_as_json(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    corpus = write_corpus(tmp_path / "corpus")
    results = write_results(tmp_path / "r.jsonl", RUNNABLE)
    assert main(["--corpus", str(corpus), "--results", str(results), "--again", str(results)]) == 0
    found = json.loads(capsys.readouterr().out)
    assert found["left_out"] == ["p/good-two"]
    assert found["every_case"]["false_rejects"]["k"] == 1
    assert found["without_the_left_out"]["false_rejects"]["k"] == 0
    assert found["changes"] == []
    assert [w["key"] for w in found["withdrawn"]] == ["p/good-gone", "p/bad-gone"]


def test_the_last_run_with_the_key_of_a_case_is_the_one_that_counts(tmp_path: Path) -> None:
    root = write_corpus(tmp_path / "corpus")
    two_runs = (
        '[[run]]\ndate = "d1"\n\n[[run.case]]\nkey = "p/bad-held"\nverdict = "FAIL"\n'
        'failing_gate = "sealed-examples"\n\n'
        '[[run]]\ndate = "d2"\n\n[[run.case]]\nkey = "p/bad-held"\nverdict = "PASS"\n'
        'failing_gate = ""\n'
    )
    (root / "held-out-run.toml").write_text(two_runs)
    held = hold_out(read_corpus(root), read_run(write_results(tmp_path / "r.jsonl", RUNNABLE)))
    assert held.with_the_key == Count(1, 1, True)


def test_a_case_that_never_ran_with_the_key_is_named(tmp_path: Path) -> None:
    root = write_corpus(tmp_path / "corpus")
    (root / "held-out-run.toml").write_text("run = []\n")
    held = hold_out(read_corpus(root), read_run(write_results(tmp_path / "r.jsonl", RUNNABLE)))
    assert held.with_the_key == Count(0, 0, True)
    assert held.not_run_with_the_key == ("p/bad-held",)


def test_a_change_of_the_first_failing_gate_alone_is_a_change(tmp_path: Path) -> None:
    first = read_run(write_results(tmp_path / "1.jsonl", RUNNABLE))
    path = write_results(tmp_path / "2.jsonl", RUNNABLE)
    path.write_text(path.read_text().replace('"visible-examples"', '"existing-tests"'))
    assert changes(first, read_run(path)) == ["p/good-two"]
