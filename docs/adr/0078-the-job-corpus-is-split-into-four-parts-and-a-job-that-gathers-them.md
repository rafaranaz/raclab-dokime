# ADR-0078 · The job corpus is split into four parts and a job that gathers them

**Status:** accepted

## Context

[ADR-0052](0052-the-corpus-runs-in-ci-in-a-job-of-its-own-with-the-network.md) runs every test of
the corpus in one job of CI, `corpus`, which is a required check of the branch `main`. It is the
longest job of CI, and it grows with each case. Four runs with `--durations=0`, in #197, twice in
#198 and in #199, gave these seconds of pytest by part:

| Part | #197 | #198 | #198, rebased | #199 |
|---|---|---|---|---|
| The audit of the six cases of mdformat | 284 | 283 | 378 | 286 |
| The hold-out by hand of B0 | 159 | 159 | 204 | 160 |
| The self-checks of the packs | 101 | 101 | 133 | 101 |
| The audit of the six cases of python-semver | 85 | 85 | 107 | 86 |
| The sealed run of B1 | 36 | 36 | 43 | 36 |
| The witnesses | 33 | 33 | 44 | 33 |
| **pytest, in all** | **700** | **703** | **911** | **699** |

Three runs lie within 4 seconds of each other; the fourth is 30 % slower in every part alike, which
points to the runner and not to a test. A case of mdformat costs about 47 seconds and one of
python-semver about 14, so the eighteen cases that B3 adds would take the audit alone from about 6
minutes to about 15.

## Decision

This amends ADR-0052 in how the job `corpus` is run; the rest of it stands.

**The tests of the corpus run in four jobs at once, and a job named `corpus` gathers them:**

| Part | What it runs |
|---|---|
| a | the audit of the cases of mdformat |
| b | the audit of the cases of python-semver and of cachetools |
| c | the hold-out by hand and the sealed run |
| d | every other test of the corpus |

- **No test is left out.** Part d runs the whole corpus with the selections of a, b and c
  deselected, so a test that none of them selects falls into d; it is the complement by
  construction, not a list. A step of the job `corpus` reads the JUnit reports of the four parts
  and demands that the number of their tests equals the number of tests of the corpus collected in
  one collection; it fails otherwise.
- **The job `corpus` fails unless the four parts end in `success`.** It needs them and runs with
  `if: always()`; a part that is skipped or cancelled fails it as one that fails. It keeps the name
  of the required check, so the rules of the branch do not change.
- **Each part runs the condition of
  [ADR-0077](0077-the-corpus-does-not-run-on-a-pull-request-that-only-changes-text.md)** as a step
  of its own: on a pull request of text its steps are skipped, not the job, which ends in
  `success`.
- **The JUnit report of the self-checks stays in the part where they run**, and
  `tools/check_corpus.py` reads it there. Each part writes its duration.
- **When a part is split again.** If a part takes more than 6 minutes of pytest in three runs in a
  row, it is split without another ADR, and the pull request that splits it says so.

## Basis

Measured on this repository: the durations of each test of the corpus in the four runs above, read
from the logs of the job.

Verified in the documentation of GitHub
([troubleshooting required status checks](https://docs.github.com/en/pull-requests/how-tos/merge-and-close-pull-requests/troubleshooting-required-status-checks)):
a job that depends on a job that failed is skipped, and a skipped job reports success, so a job
that gathers others has to run with `always()` and check their results itself.

Not checked, and to be measured in the first run with the split: how many cores the runner has,
and how much the setting up and the cloning add to each part; in #193 every step but pytest took
less than 15 seconds in all. With them, the wait for the corpus is expected to fall from about 12
minutes to about 5, the longest part; that is reasoning until measured.

## Alternatives considered

- **pytest-xdist inside the one job.** Discarded: it keeps the name of the job, but the runners
  have few cores and the corpus runs podman, where two runs at once have already given failures
  that come and go; it was not measured.
- **Require each part by its name in the rules of the branch.** Discarded: the rules would change
  each time the split changes, and a part left out of them would not block a merge.
- **Split the tests by their durations with a plugin such as pytest-split.** Discarded for now: it
  shares out better, but adds a dependency and a file of durations to keep up to date.
- **Keep one job.** Discarded: it grows to about 20 minutes with the cases of B3.

## Consequences

- **The wait for the corpus** is that of its longest part, about 5 minutes today against about 12,
  once measured; the runner time grows by the setting up and the cloning of three more jobs.
- **Growth falls on the part of each project**, and the rule of 6 minutes splits a part again
  without an ADR.
- **The check of the count** catches a test lost or run twice by a wrong selection; a test that is
  not collected at all is out of its reach, as it is today.
- **The job `corpus` no longer runs a test itself**: a failure shows in the part that ran it, and
  `corpus` says which part did not end in `success`.
- **On the acceptance** of this ADR, ADR-0052 is marked amended by it.
