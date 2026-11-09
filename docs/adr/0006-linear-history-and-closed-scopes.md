# ADR-0006 · Linear history with rebase and closed commit scopes

**Status:** accepted

## Context

The goal is to work on and review one module at a time, and to have a history that explains every
change. Conventional Commits gives messages a format, but a free scope (`fix(whatever): ...`)
guarantees nothing about what the commit touches.

## Decision

- Scopes are a closed list in `tools/scopes.toml`, each with the paths that belong to it.
- A branch declares a single scope in its name (`type/scope-description`). Its commits must use
  that scope and its changes must stay within its paths, except for the shared paths: the ADRs,
  the roadmap and `tools/scopes.toml` itself, so that a branch can declare its scope.
- Pull requests are integrated by rebase: `main` has a linear history where every commit passes
  the rules.

## Alternatives considered

- **Squash merge.** It simplifies the history, but it folds into one commit changes that were made
  and reviewed separately, and the final message does not always keep the reason for each step.
- **Merge commits.** They keep the branches, but the history stops being linear and bisectable.

## Consequences

- Opening a new module starts by declaring its scope and paths, on that module's own branch.
- A change that needs to touch two scopes is split into two branches. This is intentional: it is
  the sign that the change was not well delimited.
- Since any branch can edit `tools/scopes.toml`, it could also widen its own paths. Pull request
  review checks that a branch only adds or changes its own scope entry.
