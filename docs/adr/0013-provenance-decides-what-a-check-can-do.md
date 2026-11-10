# ADR-0013 · The origin of a check decides what its failure can do

**Status:** proposed

## Context

The principle is that mechanical gates decide and a model never does. But a model can still write
the thing a gate evaluates: a test, a property, a formalisation. Then the gate is mechanical in
name only. Tests written by models are noisy: in one study 62 % of failing generated tests were
wrong themselves; in another only 56 % of reported property failures were real defects.

## Decision

Every check carries its origin, and the origin fixes the effect of a failure:

| Origin | Where the expected result comes from | On failure |
|---|---|---|
| `human` | A person approved the input and the output | Fail |
| `derived` | A relation of the catalogue, approved by a person, applied mechanically | Fail |
| `model` | A model wrote the check or estimated the output | Ask a person |
| `existing` | The suite the project already had | Fail as a regression; marked apart |

A model may **propose** examples. They become `human` when a person approves them. Mutation score
and model review are information in the evidence, never a gate.

## Basis

Literature. [Second-model tests](https://drops.dagstuhl.de/entities/document/10.4230/LIPIcs.ESEM.2026.11),
[agentic property testing](https://arxiv.org/abs/2510.09907), mutation score of generated suites
predicting real faults poorly ([study](https://arxiv.org/abs/2607.22880)), rejected review
comments ([study](https://arxiv.org/abs/2607.03316)). Even human-curated tests reject correct
solutions ([OpenAI on SWE-bench Verified](https://openai.com/index/why-we-no-longer-evaluate-swe-bench-verified/)).

## Alternatives considered

- **Treat all hidden checks alike.** A noisy generated test would reject good changes.
- **Drop model-written checks.** They find cases nobody thought of; as questions they are useful.

## Consequences

- More questions to the person, bounded by budgets.
- The evidence shows how much of a verdict rests on human approval and how much on the rest.
