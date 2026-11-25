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
| [Decisions](../adr/README.md) | Every decision with its status; from ADR-0008 on, each states its basis and the alternatives considered |

The phases and the blocks of construction are in the [roadmap](../ROADMAP.md).

## Invariants

The strengths of the design are written as invariants
([ADR-0030](../adr/0030-the-harness-is-measured-on-a-corpus-with-known-verdicts.md)). Each one is
to have a mechanism that fails in CI when it is broken. "Enforced today by" names the requirements
that enforce it today, with what they make hold; their tests are those whose marker
`# SDD-EARS:` names them. "Not yet" says what is not built and the block or the milestone of the
[roadmap](../ROADMAP.md) that brings it; R6 gives a block to what points to it.

| Id | Invariant | Enforced today by | Not yet |
|---|---|---|---|
| INV-1 | No path leads from a model output to a `PASS` or `FAIL` without a human approval or a mechanical derivation. A passing check of origin `model` supports nothing; the suite the project already had counts as approved | VERIFY-003, VERIFY-004, VERIFY-082, VERIFY-163, CONTRACT-071, EVIDENCE-045, EVIDENCE-062: each check carries its origin, and an example of origin `model` that fails asks instead of failing | No output of a model reaches the harness until the gateway, block F. The property test on the aggregator, R6 |
| INV-2 | Code written by the agent never runs in a process that holds the expected value of a held-out example. The inputs of held-out examples do enter the verification zone, because the code has to receive them | CORE-161, SANDBOX-119, PLATFORM-092, VERIFY-191, VERIFY-192, SANDBOX-128, SANDBOX-129, SANDBOX-130, SANDBOX-131: the request of an example carries nothing of what is expected, the adapter gives the digest of the program it mounts, and the sealed batch is opened in memory; before each sealed run the gate looks for the sentinel of the batch, the impossible value of its canary, in the tree of the change and in the requests, an `ERROR` when found; and the adapter passes into the zone nothing else that a run can change, its arguments, mounts, files and environment each fixed by a test. It does not see content transformed on purpose, which is hostile code, outside the threat model | — |
| INV-3 | From the split on, no file readable from where the agent works contains held-out content in clear. For a single developer without CI this is best effort, and the evidence says so | CONTRACT-091, INTERFACES-160, INTERFACES-172, VERIFY-191, VERIFY-192, INTERFACES-190, INTERFACES-191, INTERFACES-192, INTERFACES-193: `contract seal` writes into the project only the visible contract and the sealed batch, and no file that holds the text of a held-out example, and a contract that holds an id both visible and held out is an `ERROR`; before each sealed run the gate looks for the sentinel in the tree of the change, and after it the command looks for it in all that the run wrote in `--out` and in the evidence, an `ERROR` without evidence when found, whose message says to move `--out` out of the reach of an agent | The search for the sentinel in clear before each launch of the agent, block C. It does not see content transformed on purpose, which is hostile code, outside the threat model |
| INV-4 | The aggregated verdict of a change can be recomputed from base, patch, contract, image and its platform, pack, policy, flow, seeds and the version of the harness, all identified by digest, together with what the ledger recorded of the run: the answers of people, the outputs of models and the list of unstable tests. When two runs differ, the result is `ASK` | EVIDENCE-022, EVIDENCE-023, EVIDENCE-027, INTERFACES-187, CORE-122, CORE-123, CORE-135: the evidence names the base, the policy, the image, the pack and the image of the change by digest, the seed of the relations is recorded, and the ledger is a chain that verifies | A replay command that recomputes the verdict from the ledger and the stored artifacts, sealed gates only where the key is, R6. The flow, by digest, comes with the flow file, block C |
| INV-5 | Every non-final state has an exit gate; every loop has a budget; exhausting a budget leads to a state that asks a person | INTERFACES-090, INTERFACES-092: the only flow is the audit, fixed in the code, with no loop and no budget, and a state that does not give `PASS` ends the run | The validator of the flow file, which checks the three, block C, where the flow file is first used |
| INV-6 | Nothing is delivered with an unresolved `ERROR`, and nobody can accept one | CORE-002, INTERFACES-092, INTERFACES-100, EVIDENCE-020: an `ERROR` wins the aggregation and ends the run, and the evidence says `delivered` as `false`, since nothing is delivered | The validator, which rejects a flow with a transition from `ERROR` or `FAIL` to a state that delivers, block C; delivery, block E. The property test on the aggregator, R6 |
| INV-7 | Every gate of the flow appears in the evidence as run, skipped because the policy declares it optional, not applicable, or not reached. The last two carry their reason, derived mechanically | VERIFY-121, VERIFY-122, VERIFY-127, INTERFACES-091, INTERFACES-179, EVIDENCE-040, EVIDENCE-042, EVIDENCE-046, EVIDENCE-087, EVIDENCE-088: every gate of the audit is listed as run, not applicable or not reached, with its reason, against the fixed list of gates of the audit | The check of the gates of the evidence against the list of gates of the flow file, block C. A gate skipped because the policy declares it optional, R6 |
| INV-8 | Every human decision is an event with an identity and with how that identity was established: signed, declared, or through a client and unverified. Every delegated answer is marked | INTERFACES-171: `contract seal` records the question and the answer of its confirmation, without an identity. The approval of a contract is the merge of its pull request (ADR-0067), outside dokime | The identity and how it was established, through a signature and the forge, block E. The human channel, with the delegation flag, R6 |
| INV-9 | Only `interfaces` imports an adapter. No other module does | REPO-100, REPO-103: the import contracts, which name every module of the module diagram | — |
| INV-10 | Evidence is validated by a command that depends only on the `evidence` and `core` modules, git and the public verifier of the signature scheme named in the evidence | Nothing | A test that installs only `evidence` and `core` and runs the command of validation, block E |

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

## What depends on Python

The first version verifies Python projects; Java arrives in block G. These parts of dokime assume
Python, and are the ones a second language reaches first:

- **The program that observes the examples**, of any boundary, is a program of Python,
  `sandbox/observe_program.py`, run with the `python` of the image of the project
  (`sandbox/podman.py`). The image of a project needs an interpreter of Python even to observe a
  command line.
- **The boundary `function`.** The program that observes the examples in the zone,
  `sandbox/observe_program.py`, imports the target with `importlib`, and `oracle/compare.py` reads an
  exception as `pytest.raises` reads it.
- **The tests of a file.** `verify/existing.py` ties each test to its file by the path of a module
  of Python, the path without `.py` and with `/` as `.`.
- **The configuration of the tests.** `packs/sections.py` reads the sections of a pack in the formats
  that pytest uses, TOML and INI.
- **The matcher `$fullmatch`.** Its pattern is a regular expression of Python
  ([ADR-0039](../adr/0039-what-a-contract-of-the-first-version-may-say.md)).

The gates that compare trees and patches, the ledger and the evidence do not depend on the
language of the project. Nor does the boundary `cli` in what it compares, but it does in the
program that runs it, as the first point says. This is read in the code, not tested: no project in
another language has been verified yet.

## Out of the first version

Graphical interfaces, several repositories per project, a code index with compiler precision, a
web panel, formal verification of code, and changes that are not application code (data
migrations, infrastructure).
