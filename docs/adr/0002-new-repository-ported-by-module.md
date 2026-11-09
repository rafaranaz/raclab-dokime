# ADR-0002 · New repository, ported module by module from `dokime`

**Status:** accepted

## Context

`dokime` contains a solid design (documents 01 to 08 of its analysis) and a lot of knowledge born
from real incidents, but its code is not modular in practice:

- 8 direct cycles between packages and 70 imports of private functions across packages.
- The old engine, which was meant to be retired, is still a central dependency of the new one.
- As much prose as code in production files, much of it telling the history of the code itself.
- The code knowledge graph was validated only on small examples; on a mid-size repository it
  resolves part of the ambiguous references arbitrarily and marks them as certain.

Any in-place cleanup has to touch almost everything at once, which is the way of working that led
to that situation.

## Decision

`raclab-dokime` is created empty, with its boundaries and gates defined before the first line of
code. `dokime` stays as a read-only reference. Each module is ported separately and only enters
when it meets its definition of done: EARS requirements, behaviour tests, no history in the code
and respect for the boundaries.

## Alternatives considered

- **Cleaning `dokime` in place.** The cycles and private dependencies mean every step touches
  several packages at once; there is no way to work on one module in isolation.
- **Rewriting from scratch without looking at `dokime`.** It would lose the knowledge embedded in
  the gates, which came from real failures in production runs.

## Consequences

- Two repositories coexist during the port; `dokime` receives no changes.
- Many `dokime` tests pin internal details or parity with the old engine. The behaviour they test
  is ported, not the tests as they are.
- The port order and the exit criteria of each phase are in the [roadmap](../ROADMAP.md).
