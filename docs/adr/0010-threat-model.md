# ADR-0010 · The threat model names what is defended and what is not

**Status:** proposed

## Context

Without a threat model nobody can judge whether an isolation level is enough or what a piece of
evidence is worth. A harness with the same isolation techniques was escaped in 2026 through its
own local control interface
([CVE-2026-82533](https://www.ox.security/blog/cve-2026-82533-deepseek-harness-ai-agent-sandbox-escape/)).

## Decision

| Id | Threat | In scope | Main defence |
|---|---|---|---|
| T1 | Careless agent: touches what it should not, breaks existing tests | Yes | Verification on a clean tree, regression gate |
| T2 | Opportunistic agent: fits the solution to what it sees | Yes | Comparison outside the subject's process, held-out examples |
| T3 | Repository or dependency content that injects instructions | Partly | Optional isolation; verification reads no instructions |
| T4 | Invented or malicious package requested as a dependency | Partly | Prepare phase with allowed registries and human approval |
| T5 | Hostile code aimed at the harness itself | No | Declared in the evidence |
| T6 | A user who forges their own evidence locally | No | Re-verification in CI |
| T7 | A compromised model provider | No | A local model avoids it |

Assets, in order: the user's machine and credentials, the sealed material, the integrity of the
verdict, the integrity of the evidence.

## Basis

Reasoning, plus one incident. The four techniques of T2 are the ones measured in
[ImpossibleBench](https://arxiv.org/abs/2510.20270).

## Alternatives considered

- **Not stating it.** Every later decision about isolation would be argued without a criterion.
- **Putting T5 in scope.** It needs a hardened runtime for every verification, which contradicts
  running on a developer's machine without friction.

## Consequences

- The project's existing test suite runs inside the process of the code under test, so it resists
  T1 and part of T2 only; the evidence marks it with its own origin.
- Anyone who needs T5 or T6 covered has to add controls outside this product.
