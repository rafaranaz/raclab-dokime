# SDD-EARS: BENCH-011 BENCH-012 BENCH-018
from pathlib import Path

import pytest

from dokime.bench.corpus import read_corpus
from dokime.bench.metrics import Count, counts
from dokime.bench.results import BenchError, read_run
from tests.bench.corpora import RUNNABLE, write_corpus, write_results

REPOSITORY = Path(__file__).resolve().parents[2]


def test_a_good_case_whose_witness_either_reader_labels_not_isolated_is_left_out(
    tmp_path: Path,
) -> None:
    corpus = read_corpus(write_corpus(tmp_path / "corpus"))
    assert corpus.excluded == frozenset({"p/good-two"})
    run = read_run(write_results(tmp_path / "r.jsonl", RUNNABLE))
    assert counts(corpus, run, corpus.excluded).false_rejects == Count(0, 1, False)
    assert counts(corpus, run).false_rejects == Count(1, 2, False)


def test_undecidable_counts_as_not_isolated_and_the_last_label_of_a_reader_counts(
    tmp_path: Path,
) -> None:
    undecidable = read_corpus(write_corpus(tmp_path / "u", reader_b_two="undecidable"))
    assert undecidable.excluded == frozenset({"p/good-two"})
    corrected = read_corpus(write_corpus(tmp_path / "c", reader_b_two="isolated"))
    assert corrected.excluded == frozenset()


def test_in_the_corpus_of_this_repository_only_the_case_of_w30_is_left_out() -> None:
    corpus = read_corpus(REPOSITORY / "tests" / "corpus")
    assert corpus.excluded == frozenset({"python-semver/nextver-bumps-build-only-versions"})


def test_a_reader_without_the_label_of_a_witness_stops_bench_naming_both(tmp_path: Path) -> None:
    root = write_corpus(tmp_path / "corpus")
    answer = root / "blind" / "answers" / "A-1.txt"
    answer.write_text(answer.read_text().replace("W03 | isolated | - | r\n", "W03 isolated\n"))
    with pytest.raises(BenchError) as stopped:
        read_corpus(root)
    assert "A" in str(stopped.value)
    assert "W03" in str(stopped.value)
