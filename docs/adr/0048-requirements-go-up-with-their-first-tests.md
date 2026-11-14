# ADR-0048 · Requirements go up with their first tests

**Status:** accepted

## Context

The [open-scope](../../.claude/skills/open-scope/SKILL.md) skill asked to open the pull request of
a scope as a draft with only its requirements, before writing code, so that they are reviewed
before code is built on them. The traceability gate fails when a requirement has no test, so such a
draft is always red, and a red pull request cannot be told apart from a broken one. The scopes of
`packs` (#28) and `core` (#40, #46) were built the other way: one pull request, the requirements in
one commit and the tests and code in the next. The maintainer asked for that, without the skill
being changed first.

## Decision

The requirements of a scope go up in the same pull request as their first tests, in separate
commits: the requirements first, then the tests and the code that turn them green. There is no
draft pull request with traceability red. Step 4 of the open-scope skill says so.

## Basis

Read in the history of the repository: #28 has four commits, the scope, the requirements, the check
and the rules, and its documentation; #40 has the scope, the requirements, the port and a link; #46 has the
requirements and the values. Each was merged with every gate green. Reasoning, without a test:
that a reviewer reads the requirements first because their commit comes first, and that the
review of requirements loses nothing by arriving with a test that shows what each one means.

## Alternatives considered

- **Keep the draft with only the requirements.** It is red by construction, and every scope starts
  with a pull request that cannot be merged and a check that means nothing.
- **Exempt drafts from the traceability gate.** It relaxes a gate, which needs its own ADR, for a
  pull request that is never merged as it stands.
- **Show the requirements to the maintainer outside a pull request**, in the conversation. That is
  what was done for `core` before #40, and it leaves no record in the repository.

## Consequences

- The first review of a scope comes with code. If the requirements are wrong, the tests and code of
  the second commit are thrown away with them.
- A requirement that has no test yet cannot go up, even to be discussed. It waits in the branch.
- Every pull request of a scope is green when it is opened, so a red one always means something is
  broken.
