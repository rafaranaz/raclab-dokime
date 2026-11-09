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

A critical review of the `dokime` design (its documents 01 to 08, the recorded incidents and the
measurements of its code) to settle the architecture of this repository. It is delivered in
several pull requests of the `arch` scope, reviewable separately:

1. **Context and modules.** Context diagram (C4 level 1) and module diagram with the allowed
   dependencies.
2. **States and flows.** Global state machine, composition per mode and TDD sub-machine with
   failure routing.
3. **Data and trust.** Code graph model, ledger and traceability, end-to-end sequence of a story,
   and trust boundaries (sandbox, untrusted repository, secrets).

Decisions to review with evidence, each in its own ADR:

- Code graph built on tree-sitter or on SCIP.
- Own state engine or an existing one.
- Levels of formal verification.
- MVP scope: modes, languages, dashboard and daemon.
- Delivery interface independent of GitHub.
- Bilingual interaction: how the user works in Spanish or English while internal artifacts and
  prompts stay in English ([ADR-0005](adr/0005-languages.md)).

Gates added in this phase, because they depend on the architecture:

- Import contracts between modules (import-linter), derived from the module diagram.
- Validation of the Mermaid diagrams.

Exit criteria:

- Every module has a public interface, high-level EARS requirements and a closing gate defined.
- The eight diagrams are in `docs/architecture/` and pass validation.
- The import contracts are in CI.
- The architecture is approved in review.

## Phase 2 · Module-by-module port

One module open at a time, each with its scope, its branch and its pull request, in this
provisional order (to be confirmed when phase 1 closes):

`core` → `graph` → `sandbox` → `gateway` → `verify` → `engine` (delta mode only) → `spec` →
`delivery` → `interfaces`

Initial language scope: Python and Java. Go and TypeScript come in once the core is closed.

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
