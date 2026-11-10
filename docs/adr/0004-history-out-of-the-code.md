# ADR-0004 · History lives in git and in the ADRs, not in the code

**Status:** accepted

## Context

Comments that tell how each line came to be grow until a file holds as much prose as code, cite
task identifiers and point to documents that no longer exist in the repository. Auditing what a
function does then means separating its explanation from its history.

## Decision

Comments and docstrings describe what the code does and why, in the present tense. History (what
changed, when, and because of which incident) goes in commit messages and, when it is a decision,
in an ADR. `tools/check_history.py` rejects task identifiers, versions, dates, narrative phrases and
references to missing Markdown files in comments and docstrings.

## Alternatives considered

- **A style rule without a check.** It does not survive the pressure of going fast.
- **Forbidding long comments.** Some local decisions need explaining; the problem is not length but
  text that tells history instead of behaviour.

## Consequences

- The check is heuristic: it can miss history written without recognisable markers. Pull request
  review covers that gap.
- To understand why something changed, look at `git log` or the ADRs, not at the file.
