---
name: tdd
description: The TDD cycle of this repository. Use when implementing or changing any behaviour in src/ or tools/, one requirement at a time.
---

# TDD

Every EARS requirement is built with the same cycle. Red is demonstrated, never assumed.

## Cycle

1. **Pick a requirement** from `docs/requirements/<scope>.md`. If it does not exist, write it
   first with the `ears-requirements` skill.
2. **Write the test** in `tests/<scope>/test_*.py`. The first line of the file declares the
   requirements it proves: `# SDD-EARS: CORE-001 CORE-002`.
3. **Run it and watch it fail** for the right reason.
   - A legitimate red is a behaviour assertion that is not met.
   - An `ImportError`, `NameError` or `AttributeError` is a **false red**: the test never got to
     exercise anything. Declare the minimal signature first (a function that raises
     `NotImplementedError`) and run again until the failure is about behaviour.
4. **Implement the minimum** that turns the test green. Anything beyond that has no test behind
   it.
5. **Refactor only on green.** With red tests there is no way to know whether a change broke
   something or it was already broken.
6. **Run the scope's gates** before committing: tests, lint, types and history.

## Rules

- **Green is reached in production code, never by editing the test.** If the test looks wrong,
  say so explicitly and decide with the reviewer; do not change it on your own.
- **A test proves observable behaviour**, not internal details: if a refactor that does not change
  behaviour breaks the test, the test was badly framed.
- **Error cases are requirements too.** Every `If ... then` has its negative test.
- **A failure found while using the code** first becomes a test that reproduces it, then a fix.
