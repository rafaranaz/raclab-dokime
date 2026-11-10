# ADR-0002 · New repository, ported module by module

**Status:** superseded by [ADR-0008](0008-built-new-nothing-is-ported.md)

## Context

An earlier implementation of the harness existed. Its packages depended on each other in cycles,
so any cleanup in place had to touch almost everything at once.

## Decision

This repository is created empty, with its boundaries and gates defined before the first line of
code. Each module is ported separately from the earlier implementation and only enters when it
meets its definition of done: EARS requirements, behaviour tests, no history in the code and
respect for the boundaries.

## Alternatives considered

- **Cleaning the earlier implementation in place.** Every step touches several packages at once;
  there is no way to work on one module in isolation.
- **Writing everything new.** Discarded at the time because it gave up what the earlier
  implementation had learned. [ADR-0008](0008-built-new-nothing-is-ported.md) reverses this.

## Consequences

- The part of this decision that stays in force is the empty repository with boundaries and gates
  defined first. The port does not: no module was ported, and
  [ADR-0008](0008-built-new-nothing-is-ported.md) replaces it.
