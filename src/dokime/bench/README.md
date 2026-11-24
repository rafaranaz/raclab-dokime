# bench

`bench` computes the metrics of the corpus
([ADR-0030](../../../docs/adr/0030-the-harness-is-measured-on-a-corpus-with-known-verdicts.md)) from
a file of results that a run of the corpus writes, one line of JSON for each case, and from the
data of the corpus in the repository
([ADR-0081](../../../docs/adr/0081-bench-computes-the-metrics-from-the-results-that-the-corpus-writes.md)).
It runs no audit, and needs neither the network nor podman.

```bash
uv run python -m dokime.bench --corpus tests/corpus --results results.jsonl
uv run python -m dokime.bench --corpus tests/corpus --results first.jsonl --again second.jsonl
```

The file of results of a run of CI is the artifact `corpus-results` of the job `corpus`. The
command writes JSON:

- **`every_case`**, and **`without_the_left_out`**, which leaves out each good case whose witness
  either reader of the blind reading of B3a labels, last, `not-isolated` or `undecidable`; the
  cases left out are in `left_out`. Each has the false accepts of each label of a bad case, the
  false rejects, the questions and the errors, each as `k` of `n` with whether the run had the key
  and the Wilson interval of 95 % ([Brown, Cai and DasGupta, 2001](https://projecteuclid.org/euclid.ss/1009213286)),
  `null` when `n` is 0. A case is accepted on `PASS` and rejected on `FAIL`; `ASK` is a question,
  and `ERROR` is neither.
- **`withdrawn`**: each withdrawn case with the verdict and the first failing gate of its first run,
  out of every count; a good one that failed is `false_reject_caused_by_its_contract`.
- **`hold_out`**: the false accepts of the cases labelled `fails-a-held-out-example`, in the run
  when it had no key, and in the last run with the key of each case in
  `tests/corpus/held-out-run.toml`, with the cases that no run with the key audited.
- **`changes`**, with `--again`: the cases whose verdict or first failing gate differ between two
  files of results of the same commit; files of different commits are refused.

`bench` stops with an error when a file of results gives more than one commit or differs in
whether the key was given, names a case that the corpus does not hold, or lacks one that the audit
of the corpus runs.

Its limits:

- **Without the key, `fails-a-held-out-example` gives every case as a false accept**, by design;
  `hold_out` gives that label with the key.
- **The run with the key is read from `held-out-run.toml`**, not from a file of results, so it has
  no commit, and its cases are judged on the record that the maintainer committed.
- **A file of results of a pull request records the merge commit that GitHub makes**, which does
  not exist after a merge by rebase; the figures of a version come from runs on a push to `main`.
