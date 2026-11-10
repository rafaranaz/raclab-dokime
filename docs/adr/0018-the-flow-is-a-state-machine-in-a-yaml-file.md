# ADR-0018 · The flow is a state machine declared in a YAML file

**Status:** proposed

## Context

The harness decides what comes next: prepare, baseline, approve, work, verify, ask, deliver.
A team under regulation may need a different flow from a single developer, and an auditor wants
to see the exact flow a change went through.

## Decision

- The flow is a YAML file with a strict schema: states, the gate that closes each one, the
  transition for each verdict, which states are final and which of those deliver. Unknown fields
  are rejected.
- It is validated when loaded: every non-final state has a gate; a final state is reachable from
  every state; every loop has a budget in the policy, and exhausting it leads to a state that asks
  a person; no transition leads from `ERROR` or `FAIL` to a state that delivers.
- **Exhausting a budget asks a person.** It neither rejects nor continues on its own.
- The file carries no logic. Conditions live in the gates, which are code.
- The digest of the flow is part of the evidence.

## Basis

Reasoning: flexibility per project, validation before running and the exact flow in the evidence.
A study on policy workflows supports deterministic control with a validated, frozen graph
([STAGE](https://arxiv.org/abs/2608.22538)); it is one study, in customer service, and does not
show that the graph has to be a file.

## Alternatives considered

- **A typed transition table in code**, moved to a file when a second flow exists. Less work now
  and the same validations; discarded because flows per project are wanted from the start.
- **A directed acyclic graph of steps.** It cannot express the retry loop.
- **An existing workflow standard.** They bring expression languages, which is the logic in the
  file this decision excludes.

## Consequences

- A loader, a schema and a validator have to be written before the first flow runs.
- The temptation to add conditions to the file has to be refused each time.
