# Requirements of the `bench` scope

The metrics of the corpus ([ADR-0030](../adr/0030-the-harness-is-measured-on-a-corpus-with-known-verdicts.md)),
computed from the files of results that the runs of the corpus write
([ADR-0081](../adr/0081-bench-computes-the-metrics-from-the-results-that-the-corpus-writes.md)) and
from the data of the corpus in the repository: the labels of its cases, `withdrawn.toml`, the blind
reading of B3a, `witnesses.toml` and `held-out-run.toml`. `bench` runs no audit, and needs neither
the network nor podman. Each requirement follows an EARS template and has at least one test that
declares it in its `SDD-EARS:` marker.

A case is accepted when its verdict is `PASS` and rejected when it is `FAIL`; `ASK` is a question,
and `ERROR` is counted apart, as a failure to observe is in the measurement of biometric systems.
Without the key a case labelled `fails-a-held-out-example` passes by design, so every count says
whether its run had the key.

## The files of results

- **BENCH-001** The bench shall read a run of the corpus from a file of results that gives, on each line, the commit of the run, the key of a case, its verdict, its first failing gate and whether the key was given.
- **BENCH-002** If the lines of a file of results do not all give the same commit and the same answer to whether the key was given, then the bench shall stop with an error that names the file and the values that differ.
- **BENCH-003** If a file of results names a case that the corpus does not hold, or lacks a case that the audit of the corpus runs, then the bench shall stop with an error that names the case.

## The counts

- **BENCH-004** The bench shall leave every withdrawn case out of every count.
- **BENCH-005** The bench shall give, for each label of a bad case, the number of its cases and the number of those whose verdict is `PASS`, as its false accepts.
- **BENCH-006** The bench shall give the number of good cases and the number of those whose verdict is `FAIL`, as the false rejects.
- **BENCH-007** The bench shall give the number of cases whose verdict is `ASK`, as the questions.
- **BENCH-008** The bench shall give the number of cases whose verdict is `ERROR` apart from the accepts, the rejects and the questions.
- **BENCH-009** The bench shall give with each count whether the run that it comes from had the key.
- **BENCH-010** The bench shall give, with each count of k out of n, the Wilson interval of 95 % of k/n.

## The good cases whose witness is not isolated

- **BENCH-011** The bench shall give each count twice: over every case, and leaving out each good case whose witness the blind reading of B3a labels not isolated.
- **BENCH-012** The bench shall take a witness as labelled not isolated by the blind reading when either reader gives it, as its last label, `not-isolated` or `undecidable` in `tests/corpus/blind/`, finding the witness of a good case by its commit in `tests/corpus/witnesses.toml`.
- **BENCH-018** If a reader of the blind reading gives no label for a witness of `tests/corpus/blind/draw.toml`, then the bench shall stop with an error that names the reader and the witness.

## The withdrawn cases

- **BENCH-013** The bench shall list each withdrawn case with the verdict and the first failing gate of its first run.
- **BENCH-014** The bench shall name each withdrawn good case whose first run gave `FAIL` a false reject caused by its contract.

## The hold-out and stability

- **BENCH-015** The bench shall give the value of the hold-out as the false accepts of the cases labelled `fails-a-held-out-example` in a run without the key and in the last run with the key that `tests/corpus/held-out-run.toml` gives for each case.
- **BENCH-016** When the bench is given two files of results of the same commit, the bench shall list the cases whose verdict or first failing gate differs between them.
- **BENCH-017** If the bench is given two files of results of different commits to compare, then the bench shall refuse with an error that gives both commits.
