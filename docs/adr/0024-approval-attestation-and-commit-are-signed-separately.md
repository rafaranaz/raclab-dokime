# ADR-0024 · Approval, attestation and commit are signed separately

**Status:** proposed

## Context

If the harness signs the commit automatically with the person's key, the signature proves that
the key was on the machine, not that the person reviewed anything. "Who approved what" needs more.

## Decision

| Act | Who signs | What is signed | What it shows |
|---|---|---|---|
| Approve the contract | The person, with an explicit gesture | The digest of the contract and of what was shown | Someone accepted those examples as the criterion |
| Attest the verification | The identity that ran the gates | The evidence envelope | Those gates gave that verdict on that subject |
| Publish the change | The person | The commit | Authorship, as today |

- Signing goes through the system's key agent. The harness never loads a private key, and the
  wrapper, when used, denies the agent the sockets of the key agents.
- Signed commits are required on branches, not on `main`.
- The coding agent appears as co-author of the commit.

## Basis

Reasoning. Signing through a key agent is how git already signs.

## Alternatives considered

- **One automatic signature for everything.** See the context.
- **Require signed commits on `main`.** GitHub cannot sign the commits of a rebase merge; the
  evidence is bound to the tree instead ([ADR-0023](0023-evidence-is-an-attestation-bound-to-the-tree.md)).

## Consequences

- Approving a contract takes a deliberate action each time.
- A single developer signs all three acts; the evidence labels it as self-attested.
