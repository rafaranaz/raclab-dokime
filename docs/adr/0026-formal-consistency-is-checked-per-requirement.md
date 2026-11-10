# ADR-0026 · Formal consistency is checked per requirement, and its findings ask

**Status:** accepted

## Context

A solver can find contradictions between requirements. The evidence is for control requirements
over boolean and numeric variables with a hand-made variable schema; most requirements of an
ordinary application do not fit that form. The formalisation is written by a model.

## Decision

- Contradictions that need no model are always checked ([ADR-0011](0011-contract-of-requirements-and-approved-examples.md)).
- From the first version of the specification, a solver (Z3) checks the requirements that can be
  written as rules over typed variables, one requirement at a time. The policy turns it on.
- A requirement is formalised several times with variation; formalisations that are not
  equivalent mark it as ambiguous.
- Its findings are of origin `model`: they ask a person, they do not reject.

## Basis

Literature. A solver-based audit detected 97 % to 98 % of injected defects in 64 requirements of
a medical device and flagged 18.8 % as ambiguous by comparing five formalisations; it does not
handle temporal requirements ([study](https://arxiv.org/abs/2605.13817), two specifications).

## Alternatives considered

- **A solver for every requirement.** Most would not formalise, or would be over-simplified.
- **A switch per kind of project.** Too coarse: inside one project some requirements formalise and
  others do not.
- **Findings that reject.** A rejection would rest on a formalisation nobody reviewed.

## Consequences

- A variable schema has to exist for the requirements that use the solver.
- Temporal requirements are skipped and listed as not checked.
