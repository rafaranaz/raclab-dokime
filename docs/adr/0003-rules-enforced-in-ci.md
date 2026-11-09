# ADR-0003 · Rules are enforced in CI; skills only guide

**Status:** accepted

## Context

`dokime` had a plan with exit criteria per phase and explicit stopping points. They were skipped:
about 38 weeks of plan were executed in 16 days, with the benchmarks that were meant to stop the
progress deferred. The rules were written down, but nothing prevented skipping them.

The development skills (`.claude/skills/`) describe how to work, but they are instructions: on a
day when things go fast, they can be ignored.

## Decision

Every process rule that can be checked mechanically has a gate in CI, and `main` only accepts
changes that pass all of them. Skills guide how to get through those gates; they are never the
only guarantee of a rule.

## Alternatives considered

- **Rules only in documentation and skills.** That is what failed in `dokime`.
- **Adopting a complete external methodology** (for example the Superpowers skills library). It
  would bring a second process, with its own plan format and its use of parallel subagents, which
  is exactly the kind of acceleration to avoid. The methodology skills from `dokime` are reused
  and adapted instead.

## Consequences

- Rules that cannot be checked (whether a requirement expresses the right intent, whether a
  decision is good) are left to the human review of the pull request, which is the decision gate.
- Adding a process rule means writing its check, its requirements and its tests.
