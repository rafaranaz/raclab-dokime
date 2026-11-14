# Reference architecture

*Leer en [español](README.es.md).*

raclab-dokime is a **verification and evidence layer** around coding agents. It does not write
code. It produces a contract with a person, hands the work to a coding agent the user already has,
and accepts the result only through mechanical gates
([ADR-0009](../adr/0009-verification-and-evidence-layer.md)).

## What it states, and what it does not

When it delivers a change, it states:

> Patch P, applied on commit B, in environment E, conforms to contract C approved by person X,
> according to the listed checks, each with its origin. These other checks were not made. These
> decisions were taken by a person.

It does not state that the change is correct, that the contract is complete, or that the project's
existing tests can be trusted. When the person who made the change and the person who approved are
the same, the evidence says so.

## Documents

| Document | Content |
|---|---|
| [01-context.md](01-context.md) | Who the system talks to, and the trust zones |
| [02-modules.md](02-modules.md) | Modules, ports and allowed dependencies |
| [03-data-and-evidence.md](03-data-and-evidence.md) | The contract, the ledger, the evidence and a change from end to end |
| [04-states-and-flows.md](04-states-and-flows.md) | What a flow file can say, what the validator rejects, the gates and the two starting flows |
| [glossary.md](glossary.md) | The terms the invariants and the decisions rely on |
| [Decisions](../adr/README.md) | ADRs 0008 to 0032, each with its basis and alternatives |

The phases and the blocks of construction are in the [roadmap](../ROADMAP.md).

## Invariants

The strengths of the design are written as invariants, each with a mechanism that fails in CI when
it is broken ([ADR-0030](../adr/0030-the-harness-is-measured-on-a-corpus-with-known-verdicts.md)).

| Id | Invariant | Enforced by |
|---|---|---|
| INV-1 | No path leads from a model output to a `PASS` or `FAIL` without a human approval or a mechanical derivation. A passing check of origin `model` supports nothing; the suite the project already had counts as approved | The verdict type carries the origin; a property test on the aggregator |
| INV-2 | Code written by the agent never runs in a process that holds the expected value of a held-out example. The inputs of held-out examples do enter the verification zone, because the code has to receive them | The verification runtime passes only inputs into the zone and records what it mounted and passed; before each sealed run a test searches the files, arguments and environment of the zone for a sentinel string placed as an expected value. It does not see content transformed on purpose, which is hostile code, outside the threat model |
| INV-3 | From the split on, no file readable from where the agent works contains held-out content in clear. For a single developer without CI this is best effort, and the evidence says so | Each sealed batch carries a sentinel string; a test searches for it in clear before each launch of the agent and before each sealed run. It does not see content transformed on purpose, which is hostile code, outside the threat model |
| INV-4 | The aggregated verdict of a change can be recomputed from base, patch, contract, image and its platform, pack, policy, flow, seeds and the version of the harness, all identified by digest, together with what the ledger recorded of the run: the answers of people, the outputs of models and the list of unstable tests. When two runs differ, the result is `ASK` | A replay command recomputes the verdict from the ledger and the stored artifacts. Sealed gates can be replayed only where the key is |
| INV-5 | Every non-final state has an exit gate; every loop has a budget; exhausting a budget leads to a state that asks a person | The validator of the flow file, which checks the three |
| INV-6 | Nothing is delivered with an unresolved `ERROR`, and nobody can accept one | The validator rejects a flow with a transition from `ERROR` or `FAIL` to a state that delivers; a property test on the aggregator |
| INV-7 | Every gate of the flow appears in the evidence as run, skipped because the policy declares it optional, not applicable, or not reached. The last two carry their reason, derived mechanically | When the evidence is built, its gates are checked against the list of gates of the flow file, not only against the schema |
| INV-8 | Every human decision is an event with an identity and with how that identity was established: signed, declared, or through a client and unverified. Every delegated answer is marked | A decision reaches the harness through the human channel, a signature or the forge. Each of the three records the identity and how it was established; the human channel adds the delegation flag |
| INV-9 | Only `interfaces` imports an adapter. No other module does | Import contracts |
| INV-10 | Evidence is validated by a command that depends only on the `evidence` and `core` modules, git and the public verifier of the signature scheme named in the evidence | A test that installs only those two modules and runs the command |

## How a change goes through

1. **Specify.** The harness and the person write the contract: requirements and approved examples
   ([ADR-0011](../adr/0011-contract-of-requirements-and-approved-examples.md),
   [ADR-0025](../adr/0025-the-interview-works-on-files-and-ends-by-coverage.md)).
2. **Prepare.** An image with every dependency is built
   ([ADR-0016](../adr/0016-verification-in-a-container-on-base-plus-patch.md)).
3. **Baseline.** The existing tests and the examples run on the base commit
   ([ADR-0017](../adr/0017-damage-outside-the-change-against-a-baseline.md)).
4. **Approve.** The person approves the contract after seeing the baseline; part of the examples
   is sealed ([ADR-0014](../adr/0014-hidden-checks-are-held-out-approved-examples.md)).
5. **Work.** The harness launches the installed agent, or the change arrives already made
   ([ADR-0019](../adr/0019-the-harness-launches-the-installed-agent-through-files.md),
   [ADR-0020](../adr/0020-agent-isolation-is-optional-adoption-is-a-ladder.md)).
6. **Verify.** In a container without network, on the base commit plus the patch; the comparison
   with what is expected happens outside
   ([ADR-0012](../adr/0012-examples-are-observations-at-a-boundary.md),
   [ADR-0015](../adr/0015-a-gate-returns-one-of-four-verdicts.md)).
7. **Deliver.** A commit and a signed attestation
   ([ADR-0023](../adr/0023-evidence-is-an-attestation-bound-to-the-tree.md),
   [ADR-0024](../adr/0024-approval-attestation-and-commit-are-signed-separately.md)).

## Hypotheses still to be tested

Each decision says what it rests on. These rest on reasoning and need a test before they count:

| Hypothesis | Test | Block |
|---|---|---|
| Hold-out by case detects overfitted solutions that the visible examples miss | The "value of the hold-out" metric | B |
| A person spots a wrong example planted among the proposed ones | Plant it, announced in the policy, and count | F |
| Approving two or more examples per case costs an acceptable time | Minutes of a person per contract | A, by hand |
| Most real requirements can be expressed as examples at a boundary | Share of requirements marked as having no example | A |
| An agent can start with its credential and a configuration directory made for the run | Try it with two agents on Linux and macOS | C |
| ~~A pack can be proposed from the CI configuration of a project~~ | **Discarded** by [ADR-0041](../adr/0041-the-environment-of-a-verified-project-is-a-dockerfile.md): a person writes the pack | — |

## Out of the first version

Graphical interfaces, several repositories per project, a code index with compiler precision, a
web panel, formal verification of code, and changes that are not application code (data
migrations, infrastructure).
