# ADR-0053 · The plan of work lives in the repository

**Status:** accepted

## Context

The work of the harness is planned at three levels: the blocks and their exit criteria, the
milestones of the open block with what has to be decided before each, and the strategic
orientation of the maintainer. The first two were also kept in plans outside the repository, next
to the roadmap. From 2026-11-11 those plans drifted from the repository, because no session of
work and no gate of CI read them: a session reads the repository, and the gates check only the
repository. The change directory and the chained ledger, planned for A1, were not built, and no
plan in the repository said that they were still owed.

## Decision

- **`docs/ROADMAP.md` is the only source** of the blocks, the milestones, their exit criteria and
  what has to be decided before each. What is planned and not written there is not planned.
- **The strategic orientation of the maintainer is a private document**, outside the repository,
  that repeats nothing of it: it holds what the maintainer wants and why, not milestones or
  criteria.
- **Closing a milestone updates the roadmap**: its note with what was measured, the hypotheses it
  resolved and the list "Still to decide". The skill `close-scope` says so.
- **Closing a block** leaves a reminder in its closing report to review the strategic orientation
  of the maintainer, which is the only moment the two meet.

## Basis

Observed by the maintainer: the plans kept outside the repository diverged from it from 2026-11-11,
while the roadmap, which sessions read and whose links and translation the gates check, stayed
current. Read in the repository on 2026-11-15: `core` has no change directory and no ledger,
although the module map gives the ledger to `core` and the data model places the change in
`.dokime/changes/<story>/`. Reasoning, without a test: that a plan which no reader is made to open
will drift again, and that the review at the close of a block is enough to keep the private
orientation in step.

## Alternatives considered

- **Keep the plan outside and copy it into the roadmap from time to time.** Two copies, and the
  one that is not read drifts; that is what happened.
- **Put the strategic orientation in the repository as well.** It holds the reasons of a person,
  which are not a decision of the project and are not for every reader.
- **A gate that compares the two.** The private document is not in the repository, so no gate can
  read it.

## Consequences

- A session that wants to know what comes next reads only the roadmap.
- The roadmap grows with each milestone: its note, its measured numbers and its open questions.
- What the maintainer decides in private reaches the work only when it is written in the roadmap.
- The things planned and not done, such as the change directory and the ledger, are written in the
  row of the milestone that needs them.
