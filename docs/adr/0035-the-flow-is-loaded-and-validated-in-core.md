# ADR-0035 · The flow is loaded and validated in core

**Status:** proposed

## Context

The engine, which runs a flow with its loops, budgets and agent, is built in block C
([ADR-0029](0029-build-order-starts-with-auditing.md)). Block A already produces evidence, and
the evidence lists every gate of the flow and carries the digest of the flow file (INV-7). So
block A has to read a flow file and know it is well formed, two blocks before the engine exists.

## Decision

- The schema of the flow, its loader and its validator are part of `core`. They are pure: they
  receive the text of the file and return a validated flow or the list of what is wrong.
- `engine` executes a validated flow: it follows transitions, counts budgets, asks the questions
  and packages the task for the agent.
- In block A the audit flow has no loop, and `verify` runs its states in order from the validated
  flow.

## Basis

Reasoning from the build order and from INV-7. The validator has no input or output of its own,
which is what `core` allows. No external source was looked for.

## Alternatives considered

- **Leave everything in the engine and fix the audit flow in code for blocks A and B.** The
  evidence would carry the digest of a constant, and the first real flow file would arrive
  together with the first loops, which is the riskiest moment to meet the schema.
- **Move the engine to block A.** It brings budgets, questions and the agent into the block whose
  point is to need none of them.

## Consequences

- `core` grows by a schema and a validator, and needs a YAML reader.
- The rules of the validator are tested from block A, on a flow without loops first.
- The module map changes: `core` loads and validates the flow; `engine` executes it.
