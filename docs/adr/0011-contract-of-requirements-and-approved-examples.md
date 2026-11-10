# ADR-0011 · A contract is EARS requirements plus examples approved by a person

**Status:** proposed

## Context

The contract is what the result is checked against. Requirements in prose state the intent;
something executable has to decide. With the same content, a structured format does not change
correctness; ambiguity does harm.

## Decision

- A contract holds requirements in EARS and examples. **The examples decide the verdict**; the
  requirements state the intent, give each example something to refer to and let feedback name a
  requirement without revealing an example.
- Each requirement declares its kind: `new`, `change` or `preserve`. The kind fixes what its
  examples must do before the change: fail for `new` and `change`, pass for `preserve`.
- Each example carries the label of its case (normal, empty, error…).
- A contract lives in one directory per change, with the identifier of its story, its
  clarifications and its approval. It declares what it supersedes and which existing tests it
  changes. The contract in force for a repository is the union of the delivered contracts.
- Checks that need no model run first: EARS syntax, example schema, a requirement without an
  example, two examples with the same input and different results, duplicates.

## Basis

Literature and reasoning. Format alone does not improve correctness
([study](https://arxiv.org/abs/2608.13742)); semantic ambiguity lowers it
([study](https://arxiv.org/abs/2501.04810)). EARS is kept because it gives atomic statements that
can be checked for syntax. That examples decide is reasoning.

## Alternatives considered

- **Requirements only.** Then a model has to turn prose into tests, and the gate rests on it.
- **Tests written in the project's framework as the contract.** They are code, a person cannot
  approve them without reading code, and they run inside the subject's process.

## Consequences

- A person approves more: several examples per requirement.
- A requirement that cannot be expressed as an example is allowed only with an explicit mark, and
  the evidence lists it as not checked.
