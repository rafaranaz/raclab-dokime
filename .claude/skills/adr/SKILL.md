---
name: adr
description: Write an ADR in docs/adr/. Use when taking a decision with consequences on the architecture, the tools or the process.
---

# ADR

An ADR records a decision with consequences, not a summary of what was done. If, reading it a year
from now, it is not clear why the alternative was **not** chosen, the ADR has failed.

## When to write one

- A choice is made between real alternatives and it conditions future work.
- A process rule or a CI gate changes.
- A known limitation is accepted.

It is not needed for changes whose reason fits in the commit message.

## Format

File `docs/adr/NNNN-title-in-lower-case.md`, with the next free number, its Spanish version
`docs/adr/NNNN-title-in-lower-case.es.md`, and a new row in both indexes (`docs/adr/README.md` and
`docs/adr/README.es.md`).

```markdown
# ADR-NNNN · Title that names the decision

**Status:** proposed | accepted | superseded by ADR-MMMM

## Context
The forces at play: real constraints and evidence, not wishes.

## Decision
What is chosen, in the present tense and active voice ("We use X").

## Basis
What the decision rests on: published evidence, a measurement of ours, or reasoning. Reasoning
alone is a valid basis; say that it is, and name the test that would confirm it and the block of
the roadmap where it runs.

## Alternatives considered
At least one, each with the concrete reason it was discarded.

## Consequences
The good and the bad. Every decision has a cost; if you cannot find it, you have not understood
the decision.
```

## Rules

- **One ADR, one decision.** If the title has an "and" joining two choices, it is two ADRs.
- **Accepted ADRs are not edited, they are superseded.** Changing one's mind is legitimate;
  rewriting history makes the record useless. The only thing changed in an old ADR is its status.
- **Do not repeat what the code already says.** The ADR records what the code cannot say: why this
  and not that.
- **Every ADR states its basis.** CI rejects an ADR from 0008 on without a `Basis` section, and
  one whose status differs from its row in the index.
- **Effort follows the cost of undoing.** A decision that is cheap to reverse needs a reasonable
  alternative, not the best one. One that is expensive to reverse deserves the search for
  evidence against it.
- **A decision that states or changes an invariant is checked against it** before it is accepted:
  does the invariant have one reading, does it follow from the decisions in every mode, and does
  its mechanism enforce what it says. The invariants are in `docs/architecture/README.md`.
- **An ADR is born as `proposed`** and becomes `accepted` when its pull request is approved.
