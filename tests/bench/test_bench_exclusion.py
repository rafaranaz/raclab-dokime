# SDD-EARS: BENCH-011 BENCH-012
from pathlib import Path

from dokime.bench.corpus import read_corpus
from dokime.bench.metrics import Count, counts
from dokime.bench.results import read_run
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
