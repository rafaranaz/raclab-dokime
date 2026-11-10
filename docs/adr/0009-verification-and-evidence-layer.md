# ADR-0009 · The product is a verification and evidence layer around existing coding agents

**Status:** proposed

## Context

Coding agents already write code. What is measured as weak is checking it: agents exploit the
tests they can see, and a solution that passes the visible tests often fails a held-out suite. The
tools reviewed either verify with a model, or tie the user to one vendor, or structure the work
without verifying it mechanically.

## Decision

- raclab-dokime does not write code. It produces a contract with a person, hands the work to a
  coding agent the user already has, and accepts the result only through mechanical gates.
- It works with any agent and any capable model, including a local one. The evidence records the
  agent and the model of every change; compatibility is not a promise of equal results.
- What it states when it delivers: *patch P, on commit B, in environment E, conforms to contract C
  approved by person X, according to the listed checks, each with its origin; these other checks
  were not made.* It does not state that the change is correct or that the contract is complete.
- One product serves a single developer and a regulated team. It gives both the same mechanical
  rigour and labels what it cannot equalise: whether the person who approved is someone else.

## Basis

Literature. Agents cheat on up to 76 % of deliberately impossible tasks
([ImpossibleBench](https://arxiv.org/abs/2510.20270)); the gap between visible and held-out tests
grows with task size ([SpecBench](https://arxiv.org/abs/2605.21384)); verification is a named
failure category of multi-agent systems ([MAST](https://arxiv.org/abs/2503.13657)); a study of
eleven agents finds that loop sophistication does not predict results
([Harness Engineering](https://arxiv.org/abs/2609.00006)). The last two support the direction,
not a number.

## Alternatives considered

- **Build another coding agent.** The loop is not where the measured weakness is.
- **Verify with a second model.** More than half of automated review comments are rejected by
  developers ([study](https://arxiv.org/abs/2607.03316)); a model cannot be the gate.

## Consequences

- The product is only as good as the contract a person approves; a poor contract gives a poor
  conformance, stated as such.
- Supporting many agents costs integration work that a single-agent tool avoids.
