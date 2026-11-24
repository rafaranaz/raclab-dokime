# SDD-EARS: BENCH-004 BENCH-005 BENCH-006 BENCH-007 BENCH-008 BENCH-009 BENCH-010
from pathlib import Path

import pytest

from dokime.bench.corpus import read_corpus
from dokime.bench.metrics import Count, Counts, counts, wilson
from dokime.bench.results import read_run
from tests.bench.corpora import RUNNABLE, write_corpus, write_results


def counted(tmp_path: Path, verdicts: dict[str, str], key: bool = False) -> Counts:
    corpus = read_corpus(write_corpus(tmp_path / "corpus"))
    return counts(corpus, read_run(write_results(tmp_path / "r.jsonl", verdicts, key=key)))


def test_the_false_accepts_of_each_label_leave_the_withdrawn_cases_out(tmp_path: Path) -> None:
    found = counted(tmp_path, RUNNABLE)
    assert found.false_accepts == {
        "fails-a-held-out-example": Count(1, 1, False),
        "fails-a-visible-example": Count(1, 1, False),
    }


def test_the_false_rejects_are_the_good_cases_that_fail(tmp_path: Path) -> None:
    assert counted(tmp_path, RUNNABLE).false_rejects == Count(1, 2, False)


def test_questions_and_errors_are_counted_apart_from_accepts_and_rejects(tmp_path: Path) -> None:
    verdicts = {**RUNNABLE, "p/good-two": "ASK", "p/bad-visible": "ERROR"}
    found = counted(tmp_path, verdicts)
    assert found.questions == Count(1, 4, False)
    assert found.errors == Count(1, 4, False)
    assert found.false_rejects == Count(0, 2, False)
    assert found.false_accepts["fails-a-visible-example"] == Count(0, 1, False)


def test_each_count_says_whether_its_run_had_the_key(tmp_path: Path) -> None:
    found = counted(tmp_path, RUNNABLE, key=True)
    assert found.false_rejects.key_given is True
    assert all(c.key_given for c in found.false_accepts.values())


def test_the_wilson_interval_of_known_counts() -> None:
    none = wilson(0, 10)
    assert none is not None
    assert none[0] == 0.0
    assert none[1] == pytest.approx(0.2775, abs=1e-4)
    half = wilson(5, 10)
    assert half is not None
    assert half[0] == pytest.approx(0.2366, abs=1e-4)
    assert half[1] == pytest.approx(0.7634, abs=1e-4)
    assert wilson(0, 0) is None
    assert Count(8, 8, False).interval == wilson(8, 8)
