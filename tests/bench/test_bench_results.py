# SDD-EARS: BENCH-001 BENCH-002 BENCH-003
from pathlib import Path

import pytest

from dokime.bench.__main__ import report
from dokime.bench.corpus import read_corpus
from dokime.bench.metrics import check_run
from dokime.bench.results import BenchError, Result, read_run
from tests.bench.corpora import COMMIT, RUNNABLE, write_corpus, write_results


def test_a_file_of_results_gives_the_commit_the_key_and_each_case(tmp_path: Path) -> None:
    run = read_run(write_results(tmp_path / "r.jsonl", RUNNABLE))
    assert run.commit == COMMIT
    assert run.key_given is False
    assert run.results["p/good-two"] == Result("p/good-two", "FAIL", "visible-examples")
    assert run.results["p/good-one"].failing_gate is None


def test_a_file_whose_lines_give_two_commits_is_refused(tmp_path: Path) -> None:
    path = write_results(tmp_path / "r.jsonl", RUNNABLE)
    other = write_results(tmp_path / "o.jsonl", {"p/x": "PASS"}, commit="b" * 40)
    path.write_text(path.read_text() + other.read_text())
    with pytest.raises(BenchError) as refused:
        read_run(path)
    assert str(path) in str(refused.value)
    assert COMMIT in str(refused.value)


def test_a_file_whose_lines_differ_in_the_key_is_refused(tmp_path: Path) -> None:
    path = write_results(tmp_path / "r.jsonl", RUNNABLE)
    keyed = write_results(tmp_path / "k.jsonl", {"p/x": "PASS"}, key=True)
    path.write_text(path.read_text() + keyed.read_text())
    with pytest.raises(BenchError, match="key"):
        read_run(path)


def test_a_case_the_corpus_does_not_hold_is_refused(tmp_path: Path) -> None:
    corpus = read_corpus(write_corpus(tmp_path / "corpus"))
    run = read_run(write_results(tmp_path / "r.jsonl", {**RUNNABLE, "p/unknown": "PASS"}))
    with pytest.raises(BenchError, match="p/unknown"):
        check_run(corpus, run)


def test_a_case_that_the_audit_runs_and_the_file_lacks_is_refused(tmp_path: Path) -> None:
    corpus = read_corpus(write_corpus(tmp_path / "corpus"))
    lacking = {k: v for k, v in RUNNABLE.items() if k != "p/bad-held"}
    run = read_run(write_results(tmp_path / "r.jsonl", lacking))
    with pytest.raises(BenchError, match="p/bad-held"):
        check_run(corpus, run)


def test_a_second_file_that_lacks_a_case_is_refused_naming_it(tmp_path: Path) -> None:
    corpus = write_corpus(tmp_path / "corpus")
    first = write_results(tmp_path / "1.jsonl", RUNNABLE)
    lacking = {k: v for k, v in RUNNABLE.items() if k != "p/bad-held"}
    second = write_results(tmp_path / "2.jsonl", lacking)
    with pytest.raises(BenchError, match="p/bad-held"):
        report(corpus, first, second)
