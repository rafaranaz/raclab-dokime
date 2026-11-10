# ADR-0001 · Record decisions in ADRs

**Status:** accepted

## Context

When decisions are scattered across code comments, plan documents, technical-debt logs and commit
messages, working out why something is the way it is means reading the whole history, and the
code ends up explaining its own past instead of what it does.

## Decision

Every decision with consequences is recorded as an ADR in `docs/adr/`, numbered, with context,
decision, alternatives considered and consequences. An accepted ADR is not edited: it is
superseded by a new one that says so.

## Alternatives considered

- **Living design documents that are rewritten.** They lose the reason why the alternatives were
  discarded, which is exactly what is needed when a decision is revisited.
- **Decisions in commit messages.** A good complement, but they cannot be looked up by topic and
  do not show which decisions are still in force.

## Consequences

- There is a single, short place to find out why the system is the way it is.
- Writing an ADR takes some time, so it is reserved for decisions with consequences, not for every
  change.
