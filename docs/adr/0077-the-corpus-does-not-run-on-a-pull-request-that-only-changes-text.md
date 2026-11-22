# ADR-0077 · The corpus does not run on a pull request that only changes text

**Status:** proposed

## Context

[ADR-0052](0052-the-corpus-runs-in-ci-in-a-job-of-its-own-with-the-network.md) runs the tests of
the corpus in a job of CI of their own, `corpus`, on every pull request and on every push to
`main`, and makes it a gate. The job is the longest of CI: 722 seconds in the run of #199, while the
next, `lint, types and tests`, took 365. Five jobs of `ci` are required checks of the branch `main`,
`corpus` among them.

Many pull requests change only text: of the last 40 merged, #159 to #198, nine changed only
Markdown files under `docs/` outside `docs/requirements/` (#162, #174, #175, #180, #182, #183,
#189, #194 and #195), such as a note of the roadmap or an ADR. No test of `tests/corpus` and not
`tools/check_corpus.py` reads a file of `docs/`, so such a change cannot break the corpus; yet each
of them waits for it.

A required check that does not run blocks the merge: when a workflow is skipped by a filter of
paths, its checks stay pending, while a job or a step skipped by a condition reports success.

## Decision

This amends ADR-0052 in when the job `corpus` runs its tests; the rest of it stands.

**On a pull request that only changes text, the job `corpus` does not run the tests of the
corpus.** It is decided inside the job:

- **What is text is a closed list:** a file whose name ends in `.md` under `docs/`, except under
  `docs/requirements/`. Any other file, of `src/`, `tests/`, `tools/`, `.github/` or any other
  path, runs the whole job.
- **A first step of the job lists the files changed** with `git diff --name-only --no-renames`
  against the base of the pull request, with the whole history, so that a file moved shows both
  of its paths; the steps of the corpus run on a condition on its output.
- **If the step cannot decide**, because the diff cannot be read or the base is not found, the job
  runs whole or fails; it is never skipped. The step is in the same job, not in a job of its own
  that the job `corpus` needs.
- **Only on `pull_request`.** On a push to `main` the job runs whole, so that a failure of the
  corpus shows when the change merges.
- **The summary of the job says so**: "the corpus did not run: the pull request only changes
  text", with the list of the files.

The other jobs of CI, the governance checks and the tests among them, run always.

## Basis

Measured on this repository: the durations of the jobs of the run of `ci` of #199, and the files of
the last 40 merged pull requests, read with `gh`.

Verified in the documentation of GitHub
([troubleshooting required status checks](https://docs.github.com/en/pull-requests/how-tos/merge-and-close-pull-requests/troubleshooting-required-status-checks)):
a workflow skipped by a filter of paths, of branches or by a message of a commit leaves its checks
pending and blocks the merge; a job skipped by a condition reports success; and a job that depends
on a job that failed is skipped, so it may not block the merge. The last is why the step is in the
same job. A [discussion of the community of GitHub](https://github.com/orgs/community/discussions/44490)
asks still for filters of paths that work with required checks.

Reasoning only: that `git diff --name-only` without `--no-renames` names only the new path of a
renamed file, so that moving a test to `docs/` would look like text, follows from how git detects
renames, and is checked by a test of the step when it is built.

## Alternatives considered

- **`paths-ignore` in the workflow.** Discarded: the workflow would not run, and the required check
  `corpus` would stay pending and block the merge of every pull request of text.
- **A job of its own that decides, which `corpus` needs.** Discarded: if that job failed, `corpus`
  would be skipped and report success, so the corpus would not run and the check would be green.
- **A second workflow with the same name that always succeeds**, the older workaround of GitHub.
  Discarded: two definitions of one required check, which can drift apart.
- **Skip on a push to `main` as well.** Discarded: a failure would show only on the next pull
  request that runs the corpus.
- **Keep running it always.** Discarded: about 12 minutes of runner and 6 of waiting for each pull
  request of text, nine in the last forty, for no check that text can fail.

## Consequences

- **What is gained:** on a pull request of text, about 6 minutes of waiting, since
  `lint, types and tests` becomes the longest job, and about 12 minutes of runner; nine of the last
  forty pull requests.
- **What is risked:** a failure of the corpus that does not come from the change, from the network
  or from a project of the corpus, is not seen on a pull request of text; it shows on the push to
  `main` when it merges. The concurrency of CI cancels a run in progress of the same ref
  (`cancel-in-progress`), so a push to `main` followed soon by another may lose its run, and the
  failure shows then in the run of the next push.
- **The closed list is safe only while no test of the corpus reads a Markdown file of `docs/`.** A
  test fails if one starts to.
- **With the split of the job,** decided by its own ADR after three measurements, the condition
  goes in each job the corpus is split into.
- **On the acceptance** of this ADR, ADR-0052 is marked amended by it.
