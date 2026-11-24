"""The metrics of a run of the corpus (ADR-0030, ADR-0081): false accepts per label, false rejects,
questions and errors, each with whether the run had the key and a Wilson interval; the withdrawn
cases apart; the value of the hold-out; and the cases that change between two runs."""

import math
from dataclasses import dataclass

from dokime.bench.corpus import GOOD, HELD_OUT, Corpus
from dokime.bench.results import BenchError, Run

Z = 1.959963984540054
"""The quantile of the normal distribution for an interval of 95 %."""


@dataclass(frozen=True)
class Count:
    """k cases out of n, with the Wilson interval of 95 % of k/n, none when n is 0."""

    k: int
    n: int
    key_given: bool

    @property
    def interval(self) -> tuple[float, float] | None:
        return wilson(self.k, self.n)


def wilson(k: int, n: int) -> tuple[float, float] | None:
    """The Wilson score interval of 95 % of k/n, none when n is 0."""
    if n == 0:
        return None
    p = k / n
    centre = (p + Z * Z / (2 * n)) / (1 + Z * Z / n)
    half = Z * math.sqrt(p * (1 - p) / n + Z * Z / (4 * n * n)) / (1 + Z * Z / n)
    return max(0.0, centre - half), min(1.0, centre + half)


def check_run(corpus: Corpus, run: Run) -> None:
    """Refuse a run that names a case the corpus does not hold or lacks one that the audit runs."""
    unknown = sorted(set(run.results) - set(corpus.cases))
    if unknown:
        raise BenchError(f"the results name cases that the corpus does not hold: {unknown}")
    missing = sorted(set(corpus.runnable) - set(run.results))
    if missing:
        raise BenchError(f"the results lack cases that the audit of the corpus runs: {missing}")


@dataclass(frozen=True)
class Counts:
    """The counts of a run over a set of cases."""

    false_accepts: dict[str, Count]
    false_rejects: Count
    questions: Count
    errors: Count


def counts(corpus: Corpus, run: Run, leave_out: frozenset[str] = frozenset()) -> Counts:
    """The counts of a run over the cases that the audit runs, leaving out the keys given."""
    check_run(corpus, run)
    cases = {k: c for k, c in corpus.runnable.items() if k not in leave_out}
    verdicts = {k: run.results[k].verdict for k in cases}
    labels = sorted({c.label for c in cases.values() if c.label != GOOD})
    accepts = {
        label: Count(
            sum(verdicts[k] == "PASS" for k, c in cases.items() if c.label == label),
            sum(c.label == label for c in cases.values()),
            run.key_given,
        )
        for label in labels
    }
    good = [k for k, c in cases.items() if c.label == GOOD]
    return Counts(
        false_accepts=accepts,
        false_rejects=Count(sum(verdicts[k] == "FAIL" for k in good), len(good), run.key_given),
        questions=Count(sum(v == "ASK" for v in verdicts.values()), len(cases), run.key_given),
        errors=Count(sum(v == "ERROR" for v in verdicts.values()), len(cases), run.key_given),
    )


@dataclass(frozen=True)
class Withdrawal:
    """A withdrawn case as `bench` reports it, apart from the counts."""

    key: str
    label: str
    verdict: str
    failing_gate: str | None
    key_given: bool
    false_reject_caused_by_its_contract: bool


def withdrawals(corpus: Corpus) -> list[Withdrawal]:
    """Each withdrawn case with what its first run gave (BENCH-013, BENCH-014)."""
    return [
        Withdrawal(
            w.key,
            w.label,
            w.first_run.verdict,
            w.first_run.failing_gate,
            w.key_given,
            w.label == GOOD and w.first_run.verdict == "FAIL",
        )
        for w in corpus.withdrawn
    ]


@dataclass(frozen=True)
class HoldOut:
    """The false accepts of the cases that only the hold-out catches, without the key and with
    it."""

    without_the_key: Count | None
    with_the_key: Count
    not_run_with_the_key: tuple[str, ...]


def hold_out(corpus: Corpus, run: Run) -> HoldOut:
    """The value of the hold-out (BENCH-015): the run without the key, and the last run with the
    key of each case that `held-out-run.toml` gives."""
    check_run(corpus, run)
    held = sorted(k for k, c in corpus.runnable.items() if c.label == HELD_OUT)
    without = None
    if not run.key_given:
        without = Count(sum(run.results[k].verdict == "PASS" for k in held), len(held), False)
    ran = [k for k in held if k in corpus.with_the_key]
    passed = sum(corpus.with_the_key[k].verdict == "PASS" for k in ran)
    missing = tuple(k for k in held if k not in corpus.with_the_key)
    return HoldOut(without, Count(passed, len(ran), True), missing)


def changes(first: Run, second: Run) -> list[str]:
    """The cases whose verdict or first failing gate differs between two runs of one commit."""
    if first.commit != second.commit:
        raise BenchError(
            f"the two runs are of different commits, {first.commit} and {second.commit},"
            " so they do not measure stability"
        )
    keys = sorted(set(first.results) & set(second.results))
    return [
        k
        for k in keys
        if (first.results[k].verdict, first.results[k].failing_gate)
        != (second.results[k].verdict, second.results[k].failing_gate)
    ]
