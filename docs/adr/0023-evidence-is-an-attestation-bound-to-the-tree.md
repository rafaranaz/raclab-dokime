# ADR-0023 · Evidence is an in-toto attestation bound to the resulting tree

**Status:** proposed

## Context

Evidence has to be checkable by someone who does not trust the harness. The repository merges by
rebase, and GitHub rewrites the commits when it does, so a commit identifier changes at merge.

## Decision

- Evidence is an in-toto statement in a DSSE envelope, with a predicate type of our own
  ("conformance to a contract").
- Its subject is the **digest of the resulting tree** and the digest of the patch, not the commit.
- It records, for every gate of the flow, that it ran, was skipped with a reason or did not apply;
  the origin of every check; the contract and who approved it; the environment; the agent, model,
  payment mode and adoption step; the human decisions with who took them and whether delegated.
- **What was not checked is a mandatory field**, filled mechanically.
- It carries a label of independence: self-attested, verified in CI, or verified in CI with a
  second approver.
- The ledger of a run is append-only and each event stores the hash of the previous one. The gates
  can be run again from the stored artifacts.
- A command that depends only on the evidence module verifies an evidence file.

## Basis

Own test and documented practice. On this repository, the commits of a pull request changed
identifier at the rebase merge and kept the same tree digest. GitHub states that rebase merges add
commits without signature verification
([docs](https://docs.github.com/en/authentication/managing-commit-signature-verification/about-commit-signature-verification)).
in-toto, SLSA and Sigstore are the formats existing tools use
([overview](https://todogroup.org/blog/2026-07-14-verifiable-provenance-ai-assisted-contributions/)).

## Alternatives considered

- **A format of our own.** Nobody else could verify it with standard tools.
- **Binding to the commit and merging by squash.** It loses the commit-by-commit history that
  [ADR-0006](0006-linear-history-and-closed-scopes.md) keeps.

## Consequences

- The fields of the predicate have to be fixed before the first block writes evidence.
- Integrity of the evidence says nothing about the quality of the contract.
