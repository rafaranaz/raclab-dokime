# ADR-0029 · The build order starts with auditing a change that already exists

**Status:** proposed

## Context

What differentiates the product is verification. Launching agents is the most fragile part and
the least our own: it depends on each agent, on vendor policies and on isolation.

## Decision

Seven blocks, each delivering a command someone can use, one module scope open at a time inside
it:

| Block | What is built | Modules, in order |
|---|---|---|
| A · Audit | Verify a finished patch against a hand-written contract | `core`, `contract`, `packs`, `sandbox` (verification runtime), `verify`, `evidence`, `interfaces` |
| B · Hold out | Sealed and derived examples | `oracle`, `verify`, `bench` |
| C · Launch | The harness drives an agent, with the loop and disputes | `sandbox` (work), `agents`, `engine` |
| D · Protect | Changed-line coverage, impact map, behaviour differences | `verify` |
| E · Attest | Signatures, independent verification, re-verification in CI | `evidence`, `delivery` |
| F · Specify | Interview, proposals of examples, detectors, solver | `gateway`, `spec` |
| G · Generalise | A second language, more agents, team use | `packs`, `agents`, `delivery` |

- Block C does not close until the same change completes the circuit with two agent profiles, one
  of them with an open-weight model near the frontier. From C on, every block ends with that run.
- Block A includes running the audit in CI, which is the first step of the adoption ladder
  ([ADR-0020](0020-agent-isolation-is-optional-adoption-is-a-ladder.md)). Its exit criterion is
  measured on corpus cases run as ordinary tests; `bench` automates them in block B.
- Block G exists because "any agent, any language" is a stated goal, and a goal without a block
  of its own is never checked.
- First language: Python; Java arrives in block G. A graphical interface, several repositories per project and a code
  index with compiler precision are out of the first version.

## Basis

Reasoning. Block A is the smallest slice that exercises what is our own, depends on no agent and
can be used on the pull requests of this repository from the first day.

## Alternatives considered

- **Launch an agent first.** It walks the whole circuit early, but builds the loop on a
  verification nobody has measured.
- **Specification first.** It is the hardest part for the user, but everything after it depends on
  verification working.

## Consequences

- The retry loop, where cost and leakage through feedback appear, arrives in the third block.
  Blocks B and C can be swapped if that has to be seen earlier.
- The scope is large for one person; each block has to stand on its own.
