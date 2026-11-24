# ADR-0081 · bench computes the metrics from the results that the corpus writes

**Status:** accepted

## Context

[ADR-0030](0030-the-harness-is-measured-on-a-corpus-with-known-verdicts.md) gives the module
`bench` two tasks: it "runs the harness in audit mode" on the cases of the corpus, and it computes
the metrics. Since block A the audits run elsewhere: `tests/corpus/test_corpus_audit.py` audits
each case with the command `audit`, the real git and podman, in the job `corpus` of CI, split into
six parts ([ADR-0078](0078-the-job-corpus-is-split-into-four-parts-and-a-job-that-gathers-them.md));
in the run of `main` on `00419bc` the six parts took between 205 and 417 seconds of pytest each. The run
with the key of the cases with a sealed batch can only be started by the maintainer, on their
machine, and `tests/corpus/held-out-run.toml` records it.

What an audit gave is today only a line of the log of the job, `case …: verdict …`. Nothing that a
program can read keeps it.

## Decision

This amends ADR-0030 in who runs the audits; the rest of it stands.

- **The test of the corpus runs the audits** and writes, for each case it audits, one line of JSON
  to a file of results: the key of the case, its verdict, its first failing gate, and whether the
  key was given. Each file records the commit of the repository that it ran on. The job `corpus`
  keeps the files of its parts as an artifact.
- **`bench` only computes.** It reads one or more files of results, with the data of the corpus
  in the repository: the labels of the cases, `withdrawn.toml`, the blind reading of B3a,
  `witnesses.toml` and `held-out-run.toml`. It runs no audit, and needs neither the network nor
  podman. It refuses to compare two files for stability when they ran on different commits.
- **Every count says whether the run had the key.** Without it, a case labelled
  `fails-a-held-out-example` passes by design; for that label the value of the hold-out gives both
  figures, without the key and with it.

## Basis

Reasoning, on what this repository measured: the times of the parts of the job `corpus`, and that
the run with the key needs the maintainer. Running the audits again inside `bench` would double
that time for the same verdicts, and could not run the cases with a sealed batch with the key in
CI, where the key is not ([ADR-0073](0073-the-key-of-the-hold-out-lives-outside-ci-until-b4.md)).
Computing on files that the run writes is what makes the computation a test of its own, with no
network.

## Alternatives considered

- **`bench` runs the audits, as ADR-0030 says.** Discarded: it duplicates the test of the corpus,
  which has to run in CI anyway as its gate, and doubles its time.
- **`bench` reads the logs of CI.** Discarded: a log is text for a person, its format is not a
  contract, and reading it needs the API of GitHub.
- **The test of the corpus computes the metrics itself.** Discarded: the test judges each case
  against its expected verdict; the metrics need every case of a run, two runs for stability, and
  the run with the key, which no single test sees.

## Consequences

- `bench` is cheap and tested without the network; stability needs two files of results of the
  same commit, which means running the job `corpus` again.
- The format of the file of results, the commit it ran on included, is a contract between the test
  of the corpus and `bench`, and changes in both at once.
- An artifact of CI expires, so the files of results that the figures of a version rest on have to
  be kept with that version.
- The minutes of a person per change, a metric of ADR-0030, are not computed by B3e.
