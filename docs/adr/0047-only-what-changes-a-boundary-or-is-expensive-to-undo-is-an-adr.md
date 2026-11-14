# ADR-0047 · Only what changes a boundary or is expensive to undo is an ADR

**Status:** proposed

## Context

The [adr](../../.claude/skills/adr/SKILL.md) skill asked for an ADR whenever "a choice is made
between real alternatives and it conditions future work". Almost every choice fits that sentence.
In six days the repository gathered 45 ADRs and 1,834 lines of product code. Milestone A2 has five
ADRs, of 6,434 words, and no line of the package runs `git` or a container yet. Limits, error
codes and how a file is opened were decided in prose before any code tried them.

## Decision

Only a decision that does one of these is an ADR: it changes an invariant, the boundary of a
module, the contract of a port, a dependency, or a process rule or a CI gate; or it is expensive to
undo. Everything else, such as the value of a limit, an error code, a detail of implementation or
how a file is opened, is an EARS requirement of its scope, with its test, and the reason for a value
goes in the commit that sets it. If in doubt, the ADR is not written: the maintainer is asked, with
a recommendation. The rule is written in the adr skill.

## Basis

Counted in the repository on 2026-11-14, before the skeleton of A2 began: the 45 ADRs from
2026-11-09 to ADR-0045, the words of ADR-0041 to ADR-0045, the lines of `src/dokime`, and that no
module of the package starts a process. Two audits read by the maintainer, not by this ADR, found
that ADRs are written before trying, and that 5 of 6 revisions of an ADR came two days or less after
its acceptance. Reasoning, without a test: that a requirement with its test holds a limit or a code
better than prose, because the test fails when the value stops holding. The test that would confirm
the rule is the rest of A2: how many ADRs it needs, and how many of them are revised.

## Alternatives considered

- **Keep the skill as it was.** That is what led to the count above.
- **A limit of size per ADR.** A short ADR about a detail is still a detail decided before trying
  it.
- **No ADR until a milestone closes.** It holds for the rest of A2 by the decision of the
  maintainer, and as a rule it would block a change of a port or a dependency that is needed now.

## Consequences

- Limits, codes and details live in the requirements of their scope, where a test checks them.
  Their history is the history of the requirement and of the commits that change it.
- "A known limitation is accepted" is no longer a reason of its own: a limitation goes in the
  consequences of the ADR that causes it, or in a requirement.
- More questions reach the maintainer when it is unclear whether a decision crosses a boundary.
- A decision hidden in a requirement that should have been an ADR is caught only in review.
