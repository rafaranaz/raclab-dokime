# ADR-0054 · The policy is an optional file of values, and the first version holds two

**Status:** accepted

## Context

Several accepted decisions leave a value to the policy, and the evidence records the policy by its
digest ([ADR-0023](0023-evidence-is-an-attestation-bound-to-the-tree.md)). No decision says yet
what the file is. Read in the ADRs, by the block that needs each value:

| Value | Where | Block |
|---|---|---|
| How many times the baseline runs, "twice to start with" | ADR-0017 | A |
| How many times the verification runs, for the gate `repeatability` | `docs/architecture/04-states-and-flows.md` | A |
| Which gates may be skipped | ADR-0015 | D (the only example is coverage) |
| The threshold of coverage of changed lines | ADR-0017 | D |
| The budgets of the loops of the flow | ADR-0018 | C |
| The wrapper of the agent | ADR-0020 | C |
| Formal consistency; the planted example | ADR-0026; architecture | F |

## Decision

- **The file is `.dokime/policy.yaml`, and it is optional.** Without it, the defaults that `core`
  defines apply.
- **The first version holds two values**:

  ```yaml
  format: 1
  baseline:
    runs: 2
  verification:
    runs: 2
  ```

  Both are whole numbers of at least 2: with one run, an unstable test or a verdict that varies
  cannot be seen.
- **It is read by the strict reader** of [ADR-0037](0037-a-contract-is-read-by-strict-rules-of-its-own.md),
  with closed fields: an unknown field is a finding, not a silent default.
- **The evidence records the effective policy**, the one read from the file or the defaults, by
  the digest of its normalised form, and says which of the two it was. The verdict can then be
  recomputed (INV-4).
- **Each later block adds the field it needs, with a default**, so that a policy written before
  stays valid. While fields are only added, the format stays 1.
- **The limits of a build, a run and the reading of a report are not in it.** They stay the
  defaults of `core` that the caller passes
  ([ADR-0045](0045-a-test-report-is-read-by-a-bounded-reader-that-refuses-any-dtd.md)); they enter
  the policy when a project needs other values.

## Basis

Read: the ADRs in the table above. Codecov keeps its configuration in an optional file of the
repository over defaults ([Codecov](https://docs.codecov.com/docs/codecov-yaml)), and a project
built an action because Codecov does not say when that file is broken
([action-check-codecov-config](https://github.com/formsort/action-check-codecov-config)); the
strict reader answers that. A language of rules such as Rego is chosen when the logic of a policy is
complex ([comparison](https://www.techplained.com/kyverno-vs-opa-gatekeeper)); this policy is two
numbers. Reasoning, without a test: that an optional file lowers the first step of adoption, and
that recording the effective policy keeps the evidence complete without it.

## Alternatives considered

- **A required file.** One more file to write before a first audit, for two numbers that have
  defaults.
- **A language of rules.** There are no rules to write.
- **Every field now**, for blocks C, D and F. Decided before the blocks that would try them.
- **The values as options of the command.** Not protected, and easy to change in one run without
  a trace in the repository.

## Consequences

- A3 reads the policy, or its defaults, and records it in the evidence.
- A field added by a later block comes with its default and its requirement.
- The policy is already a protected path
  ([`03-data-and-evidence.md`](../architecture/03-data-and-evidence.md)); nothing changes there.
