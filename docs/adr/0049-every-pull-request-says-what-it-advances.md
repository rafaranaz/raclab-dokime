# ADR-0049 · Every pull request says what it advances

**Status:** accepted

## Context

By 2026-11-14 milestone A2 had five ADRs and no code that ran `git` or a container. Its exit
criterion is "The packs of the three repositories build and pass their self-check", and much of the
work of those days decided details that did not bring it closer. Nothing in a branch or a pull
request asked which criterion or requirement the work was for.

## Decision

Every pull request starts its description with a line **Advances:** that names the exit criterion
of the open milestone, or the requirements, that it moves forward. If it advances none, the
maintainer is asked before it is written. The pull request template has the line, and the section
on pull requests of [CONTRIBUTING.md](../../CONTRIBUTING.md) states the rule.

## Basis

Read in the descriptions of the pull requests: from #39 to #49 every one has started with that line,
except #42, which another session opened and which was closed. Four of them, #39, #45, #47 and #48,
say that they advance no exit criterion, or none directly, and the maintainer had asked for each.
Reasoning, without a test: that writing the line before the work makes a branch that serves no
criterion visible while it is still cheap to drop. The test that would confirm it is the rest of A2:
how many pull requests say they advance nothing, and whether they were asked for.

## Alternatives considered

- **Leave it to review.** Review sees the work once it is done, which is when dropping it costs
  most.
- **A check of CI that refuses a description without the line.** It would check that the line
  exists, not that what it says is true. It can be added if the line starts to be forgotten.
- **Link every pull request to an issue or a GitHub milestone.** It adds a second place to keep
  up to date, and the milestones and their criteria already live in the roadmap.

## Consequences

- A reviewer reads first what the pull request is for, and can stop there.
- Work on the repository itself, such as a process rule, advances no criterion of a milestone. The
  line says so, and the maintainer has asked for it.
- The rule depends on the line being honest. Nothing checks it but review.
