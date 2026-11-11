# ADR-0034 · A state closes with the aggregated verdict of its gates

**Status:** proposed

## Context

[ADR-0018](0018-the-flow-is-a-state-machine-in-a-yaml-file.md) speaks of "the gate that closes"
each state, in the singular. [ADR-0015](0015-a-gate-returns-one-of-four-verdicts.md) aggregates
the verdicts of the gates of a round: any `FAIL` drops the `ASK` of that round. Writing the first
flows showed that the two do not fit if a state has exactly one gate. Verification is several
gates whose verdicts have to be seen together, and the evidence has to list each one.

## Decision

- A work state lists one or more gates. They all run, in the order written.
- The state closes with the aggregation of their verdicts by the precedence of ADR-0015, and the
  flow follows the transition for that result.
- The evidence lists every gate on its own, with its status.
- Where ADR-0018 says "the gate that closes each one", it is read as "the gates that close each
  one".

## Basis

Reasoning from two accepted decisions. With one gate per state, a `FAIL` in a later state could
not drop an `ASK` raised in an earlier one, because the flow would already have stopped to ask;
aggregation by round needs the round to be a unit of the flow. No external source was looked for:
it is a point of internal coherence.

## Alternatives considered

- **One gate per state, as written.** Each gate becomes a state. Aggregation then needs the flow
  to carry verdicts from one state to the next, which is logic in the file.
- **One composite gate per state.** Verification would be a single gate with parts. The evidence
  could not say that an optional part was skipped, which INV-7 requires gate by gate.

## Consequences

- The schema of the flow has a list of gates per state.
- A flow can group or split gates into states to decide when a person is asked.
- The gates of a state run even after one of them fails, so the feedback covers the whole round.
