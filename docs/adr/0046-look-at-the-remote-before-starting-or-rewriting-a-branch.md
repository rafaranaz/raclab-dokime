# ADR-0046 · Look at the remote before starting or rewriting a branch

**Status:** proposed

## Context

More than one session, of the maintainer or of an agent, works on this repository at once, and
none sees what another has not pushed. On 2026-11-13 and 2026-11-14 that cost four times:

- The acceptance of ADR-0042 was prepared in two branches, `docs/arch-accept-repository-port`
  (#32, merged) and `docs/arch-accept-adr-0042`, deleted without a pull request.
- The acceptance of ADR-0043 was opened as #35 by one session and started by another, which the
  maintainer stopped before its commit.
- `docs/arch-run-engines` (#34), already pushed, was rebased and fixed by one session while another
  was preparing its own rebase of the same branch to push with `--force-with-lease`.
- The acceptance of ADR-0044 was opened twice, #41 and #42, sixteen seconds apart. #42 was closed.

## Decision

Before starting a branch, before rewriting one that is already on the remote, and before a commit
that changes the status of an ADR, the open branches and pull requests of the remote are listed
(`git fetch --prune`, `git branch -r`, `gh pr list`). If one already does the same work, the new
one is not started, or is started from it. The rule is written in the section on branches of
[CONTRIBUTING.md](../../CONTRIBUTING.md) and in the working rules of
[CLAUDE.md](../../CLAUDE.md), which every session loads.

## Basis

The four cases above, read in the list of pull requests of the repository and in the reflog of
one of the sessions:

- In the first, #32 had been open for six minutes when the second branch was started.
- In the second, #35 was open when the other session started.
- In the third, which push came first is not recorded.
- In the fourth, the session of #41 had listed the remote just before opening it, and #42 came
  sixteen seconds later.

A listing would have shown the first two. It cannot show work that is not pushed yet.

Reasoning, without a test: that the listing removes most duplicates at the cost of two commands.
The test that would confirm it is counting the duplicate branches and pull requests over the rest
of block A, with the rule in force.

## Alternatives considered

- **No rule; review closes the duplicates.** That is what happened in the four cases. Each one
  cost a branch, a pull request or a rebase that someone had to notice and throw away.
- **One session at a time.** It removes the problem and the parallel work the maintainer wants.
- **A check of CI that refuses a pull request changing the status of an ADR that another open pull
  request changes.** It acts only once both are open, after the work is done. It may be added
  later if duplicates go on.
- **Claim the work first**, with an issue or an empty draft pull request, before writing anything.
  It adds a step to every branch, and two claims made seconds apart race just like #41 and #42.
- **Rely on `--force-with-lease`.** It refuses a push that would discard commits someone else
  pushed, and only that: it does nothing for two branches doing the same work.

## Consequences

- Every branch, every rewrite of a pushed branch and every change of status starts with two
  commands. Without `gh`, the pull requests are looked at on the web.
- Two sessions that start the same work within seconds still collide, as #41 and #42 did. The rule
  makes that rare; it does not prevent it.
- A rewrite still uses `--force-with-lease`, which covers what a listing cannot: commits pushed
  between the listing and the push.
