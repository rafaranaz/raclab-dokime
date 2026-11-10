# ADR-0023 · Evidence is an in-toto attestation bound to the resulting tree

**Status:** accepted

## Context

Evidence has to be checkable by someone who does not trust the harness. The repository merges by
rebase, and GitHub rewrites the commits when it does, so a commit identifier changes at merge.

## Decision

- Evidence is an in-toto statement in a DSSE envelope, with a predicate type of our own
  ("conformance to a contract").
- Its subject is the **digest of the resulting tree** and the digest of the patch, not the commit.
- It records, for every gate of the flow, that it ran, was skipped because the policy declares it
  optional, did not apply or was not reached, the last two with a reason derived mechanically from
  the contract, the level of the pack or the gate that stopped the flow.
- It records the origin of every check; the contract and who approved it; the digests of the image
  with its platform, the pack, the policy and the flow; the seeds; the version of the harness; the
  agent, model, payment mode and adoption step; and the human decisions with who took them, how
  that identity was established and whether delegated. For sealed checks it carries digests and
  classes of failure, never values or inputs.
- **What was not checked is a mandatory field**, filled mechanically.
- It carries a label of independence: self-attested, verified in CI, or verified in CI with a
  second approver.
- The ledger of a run is append-only and each event stores the hash of the previous one. It keeps
  the answers of people, the outputs of models and the list of unstable tests, so a replay command
  can run the gates again from the stored artifacts without asking anyone. Sealed gates can be
  replayed only where the key is.
- Evidence is produced for every finished run, whatever its verdict, and attested the same way. A
  rejected change has evidence and no delivery.
- A command of its own, which depends only on the `evidence` and `core` modules, verifies an
  evidence file. It checks the signatures against the list of allowed signers
  ([ADR-0024](0024-approval-attestation-and-commit-are-signed-separately.md)), the schema, that
  the digest of the subject matches the tree, the chain of the ledger, and the gates against the
  flow file. It runs nothing again; that is the replay.

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
