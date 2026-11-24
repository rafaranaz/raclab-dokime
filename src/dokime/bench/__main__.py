"""`python -m dokime.bench`: the metrics of a run of the corpus, as JSON."""

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any

from dokime.bench.corpus import read_corpus
from dokime.bench.metrics import (
    Count,
    Counts,
    changes,
    check_run,
    counts,
    hold_out,
    withdrawals,
)
from dokime.bench.results import BenchError, read_run


def _count(count: Count | None) -> dict[str, Any] | None:
    if count is None:
        return None
    return {"k": count.k, "n": count.n, "key_given": count.key_given, "interval": count.interval}


def _counts(found: Counts) -> dict[str, Any]:
    return {
        "false_accepts": {label: _count(c) for label, c in found.false_accepts.items()},
        "false_rejects": _count(found.false_rejects),
        "questions": _count(found.questions),
        "errors": _count(found.errors),
    }


def report(corpus_directory: Path, results: Path, again: Path | None) -> dict[str, Any]:
    """The metrics of a run, and the cases that change in a second run of the same commit."""
    corpus = read_corpus(corpus_directory)
    run = read_run(results)
    held = hold_out(corpus, run)
    found: dict[str, Any] = {
        "commit": run.commit,
        "key_given": run.key_given,
        "every_case": _counts(counts(corpus, run)),
        "left_out": sorted(corpus.excluded),
        "without_the_left_out": _counts(counts(corpus, run, corpus.excluded)),
        "withdrawn": [asdict(w) for w in withdrawals(corpus)],
        "hold_out": {
            "without_the_key": _count(held.without_the_key),
            "with_the_key": _count(held.with_the_key),
            "not_run_with_the_key": list(held.not_run_with_the_key),
        },
    }
    if again is not None:
        second = read_run(again)
        check_run(corpus, second)
        found["changes"] = changes(run, second)
    return found


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m dokime.bench", description=__doc__)
    parser.add_argument("--corpus", type=Path, required=True, help="the directory of the corpus")
    parser.add_argument("--results", type=Path, required=True, help="a file of results")
    parser.add_argument("--again", type=Path, help="a second file of results of the same commit")
    arguments = parser.parse_args(argv)
    try:
        found = report(arguments.corpus, arguments.results, arguments.again)
    except (BenchError, OSError) as error:
        sys.stderr.write(f"bench: {error}\n")
        return 1
    sys.stdout.write(json.dumps(found, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
