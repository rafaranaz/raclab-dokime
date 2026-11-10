# Roadmap

*Leer en [español](ROADMAP.es.md).*

Each phase has exit criteria. **The next phase does not open until the previous one meets all of
them** ([ADR-0003](adr/0003-rules-enforced-in-ci.md)). If a criterion turns out to be impossible or
wrong, it is changed here in its own pull request with its reason, not skipped.

## Phase 0 · Working agreement and gates — done

Working rules, CI pipeline and development skills, with no harness code.

Exit criteria:

- [x] Reproducible environment: pinned Python, dependencies in `uv.lock`, installed with
  `--locked`.
- [x] Quality, governance, discipline and audit gates in CI, each with EARS requirements and tests
  ([docs/requirements/repo.md](requirements/repo.md)).
- [x] Working agreement documented in [CONTRIBUTING.md](../CONTRIBUTING.md).
- [x] ADRs for the process decisions.
- [x] Development skills in `.claude/skills/`.
- [x] Documentation in English and Spanish, with translations checked in CI.
- [x] CI green on the phase pull request in GitHub.
- [x] Protection of `main` enforced in GitHub (see below).

## Phase 1 · Reference architecture

The architecture of the product, decided with evidence. Every decision is an ADR that states what
it rests on (literature, reasoning or a test) and the alternatives considered
([ADR-0008](adr/0008-built-new-nothing-is-ported.md)). It is delivered in several pull requests of
the `arch` scope, reviewable separately:

1. **Map and decisions.** What the product is and states, the invariants, the context, the trust
   zones, the modules with their allowed dependencies, and the ADRs 0008 to 0032.
2. **States and flows.** The state machine, its composition per mode, the verification pipeline
   with its failure routes and the budgets.
3. **Data and evidence.** The contract and example formats, the evidence predicate, the ledger and
   the end-to-end sequence of a change.

Each module gets its high-level EARS requirements when its scope is opened in phase 2.

Gates added in this phase, because they depend on the architecture:

- Import contracts between modules (import-linter), derived from the module diagram.
- A check that every ADR states its basis.

Exit criteria:

- The documents above are in `docs/architecture/` and their diagrams pass validation.
- Every ADR from 0008 on is accepted or explicitly left as a hypothesis with its test.
- The import contracts are in CI.
- The architecture is approved in review.

## Phase 2 · Construction in blocks

Six blocks, each delivering a command someone can use
([ADR-0029](adr/0029-build-order-starts-with-auditing.md)). Inside a block, one module scope is
open at a time, in the order listed. A block closes when its exit criterion, a number measured on
the corpus ([ADR-0030](adr/0030-the-harness-is-measured-on-a-corpus-with-known-verdicts.md)), is
met and published.

| Block | Modules, in order | Exit criterion |
|---|---|---|
| A · Audit | `core`, `contract`, `packs`, `sandbox` (verification runtime), `verify`, `evidence`, `interfaces` | No false accept on patches that fail visible examples, edit tests or break existing tests |
| B · Hold out | `oracle`, `verify`, `bench` | No false accept on the four cheating techniques; value of the hold-out measured |
| C · Launch | `sandbox` (work), `agents`, `engine` | The same change completes the circuit with two agent profiles, one with an open-weight model |
| D · Protect | `verify` | Injected regressions in covered code are detected; rate of questions measured |
| E · Attest | `evidence`, `delivery` | Someone without the harness installed verifies an evidence file |
| F · Specify | `gateway`, `spec` | Minutes of a person per contract measured; the attention test done |

Initial language: Python. Java is the second.

Exit criteria for each module: the definition of done in
[CONTRIBUTING.md](../CONTRIBUTING.md#definition-of-done-for-a-scope).

## GitHub settings

Settings that live in GitHub and cannot be versioned in the repository. The repository is public,
which is what makes GitHub enforce the ruleset on a personal account.

A ruleset on `main` (Settings → Rules → Rulesets):

- Pull request required to merge, with *Rebase* as the only merge method. No approval count is
  required, because GitHub does not let authors approve their own pull requests; merging is the
  approval.
- The four CI checks must pass (`lint, types and tests`, `governance checks`,
  `commits and branch scope`, `dependency audit`), on a branch that is up to date with `main`.
- Linear history required; force pushes and deletion blocked.
