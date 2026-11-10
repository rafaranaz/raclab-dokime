# ADR-0008 · The product is built new; nothing is ported

**Status:** proposed

## Context

[ADR-0002](0002-new-repository-ported-by-module.md) planned to port an earlier implementation
module by module. Reviewing the design showed that several decisions had been carried over from
that implementation as if they were settled, without checking how existing tools, standards and
published studies handle the same problems. Three independent reviews of the design then changed
its centre: the oracle, the order of construction and the role of the coding agent.

## Decision

- Every module is designed and written new, from its requirements.
- No document, comment or commit of this repository cites an earlier implementation as a reason.
  A decision rests on literature, on reasoning or on a test, and says which.
- This ADR supersedes ADR-0002.

## Basis

Reasoning. An earlier implementation shows that an idea can be written, not that it works.

## Alternatives considered

- **Port module by module (ADR-0002).** It keeps the cost low, but it also keeps the assumptions
  nobody verified, and the design that came out of the reviews no longer matches the old modules.
- **Port only the parts that still fit.** Deciding which parts fit needs the same verification as
  writing them, without the benefit of starting from requirements.

## Consequences

- More code to write, and no shortcut for the first block.
- Each decision can be traced to its basis instead of to a previous habit.
- The accepted ADRs 0001 to 0007 keep their original context, as accepted ADRs are not edited.
