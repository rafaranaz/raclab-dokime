# ADR-0036 · A milestone may open an increment of a later module

**Status:** accepted

## Context

[ADR-0029](0029-build-order-starts-with-auditing.md) lists the modules of each block in order, one
module scope open at a time. In block A `interfaces`, where the commands live, is the last one.
The first milestone with code, A1, delivers a command that validates a contract, and its logic
needs only `core` and `contract`. Followed to the letter, the order leaves A1 with nothing a
person can run until the whole block is built.

## Decision

- The order of ADR-0029 is the order in which the modules of a block are opened for their main
  work.
- A milestone may open, ahead of that order, an increment of a later module when what the
  milestone delivers cannot be shown without it. The increment holds only what that delivery
  needs.
- One module scope is still open at a time, and the roadmap names the increment in the row of the
  milestone.
- A1 opens `interfaces` for the command `contract check` alone. A3 opens it again for `audit`.

## Basis

Reasoning. ADR-0029 chose the order so that every block delivers a command someone can use; an
increment opened early serves that same aim inside a block. No external source was looked for: it
is a point of internal coherence between the plan and the module table.

## Alternatives considered

- **Keep the order and deliver A1 as a library.** The validation is tested, but nobody can run it
  until A3, and the hand-written contracts of the corpus are checked by test code only.
- **Put the command in `contract`.** It breaks the rule that `interfaces` is the only place with
  commands and the composition root ([ADR-0031](0031-modules-depend-only-on-core.md)).

## Consequences

- `interfaces` exists from A1, with one command and no domain logic.
- A module can have several increments inside a block; each is a scope opened and closed with its
  own requirements.
