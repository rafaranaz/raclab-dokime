---
name: open-scope
description: Open the work on a new scope (a harness module or a governance piece). Use before writing any code for that scope.
---

# Open a scope

## Before starting

1. **Check that no other module is open.** Only one at a time
   ([docs/ROADMAP.md](../../../docs/ROADMAP.md)). If there is one, stop and ask.
2. **Check that the phase allows it.** If the scope is not in the current phase of the roadmap,
   stop and ask.
3. **Read the module's architecture** in `docs/architecture/`, once it exists: its interface, its
   allowed dependencies and its closing gate.

## Steps

1. **Create the branch** from an up-to-date `main`: `type/scope-description`
   (for example `feat/core-config-loading`).
2. **Declare the scope** in `tools/scopes.toml` with its paths: `src/dokime/<scope>/**`,
   `tests/<scope>/**` and `docs/requirements/<scope>.md`. This is the first commit of the branch.
3. **Write the requirements** in `docs/requirements/<scope>.md` with the `ears-requirements` skill,
   and run them through `uv run python -m tools.check_ears`.
4. **Open the pull request as a draft** with the requirements, before writing code. Reviewing
   requirements is far cheaper than reviewing code built on the wrong requirements.
5. **Build one requirement at a time** with the `tdd` skill.

## While working

- **Do not touch anything outside the scope's paths.** If it is needed, it is another branch.
  `check_scope` rejects it anyway.
- **If the scope changes** (an unplanned requirement, a dependency the architecture does not
  allow, a problem in another module), stop and ask. Do not resolve it silently.
- **Small commits**, each with its reason and every gate green.
