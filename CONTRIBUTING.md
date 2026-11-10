# How we work on raclab-dokime

*Leer en [español](CONTRIBUTING.es.md).*

The harness rests on one principle: **every step is proposed by someone (an agent or a person) and
accepted or rejected by a mechanical check**. This repository applies the same principle to its own
development. The rules in this document do not depend on goodwill: each one has a gate in CI that
checks it.

| Harness principle | How it applies here |
|---|---|
| Decision + mechanical verification | Everything goes through a pull request; it is merged only with CI green and human approval |
| EARS contract | Each scope has its requirements in `docs/requirements/<scope>.md` before any code |
| Requirement ↔ test traceability | Every test file declares which requirements it proves; CI fails if any is left without a test |
| Bounded blast radius | Every branch declares one scope and CI rejects changes outside its paths |
| Decision record | ADRs in `docs/adr/`; history lives in git, not in the code |
| Exit criteria | Each phase of [docs/ROADMAP.md](docs/ROADMAP.md) has its own; the next one does not open until they are met |

## Lifecycle of a scope

A scope is a harness module (`core`, `contract`, `verify`...) or a governance piece (`repo`, `arch`).
The closed list is in [tools/scopes.toml](tools/scopes.toml), with the paths that belong to each.

1. **Open.** Declare the scope in `tools/scopes.toml`, create the branch and write the EARS
   requirements. See the [open-scope](.claude/skills/open-scope/SKILL.md) skill.
2. **Build with TDD.** Every requirement goes through a demonstrated red test before its
   implementation. See the [tdd](.claude/skills/tdd/SKILL.md) skill.
3. **Close.** Run every gate locally, write the closing report and open or update the pull
   request. See the [close-scope](.claude/skills/close-scope/SKILL.md) skill.

**Only one module scope is open at a time**, and it belongs to the block of the
[roadmap](docs/ROADMAP.md) that is open. The next one does not open until the previous one is
merged. Governance scopes (`repo`, `arch`) may be open next to it.

## Branches

- `main` is protected: no direct pushes, only merges through pull requests with CI green.
- Format: `type/scope-description`, lower case with hyphens. For example
  `feat/contract-example-schema` or `docs/arch-c4-context`.
- `type` is a Conventional Commits type and `scope` is one from `tools/scopes.toml`. Scopes have no
  hyphens, because the first hyphen separates the scope from the description.
- Branches are short-lived: if a branch grows beyond what can be reviewed in one sitting, it is
  split.
- Merges are done **by rebase**: the history of `main` is linear and every commit is kept. When
  GitHub asks to update a branch, choose **Update with rebase**: the default option adds a merge
  commit, which the commit check rejects.

## Commits

[Conventional Commits](https://www.conventionalcommits.org/) format, in English:

```
type(scope): imperative description in lower case

Body explaining WHY the change is needed: the problem, the constraint or
the decision behind it. What changed is already in the diff.

Optional-Trailer: value
```

- `type`: `build`, `chore`, `ci`, `docs`, `feat`, `fix`, `perf`, `refactor`, `revert`, `style`, `test`.
- `scope` is required and must be the scope of the branch.
- The header is at most 72 characters long.
- `feat`, `fix`, `refactor` and `perf` need a body. Trailers (`Co-Authored-By:`...) do not count as
  a body.
- A commit is a logical, self-contained unit of change, not the dump of a work session.
- There are no merge commits on branches: they are rebased onto `main`.

## Pull requests

- Small enough to review in one sitting. The template asks for the scope and the affected
  requirements, and lists only the points a review has to judge. It has no checkbox for anything
  CI already enforces: a manual tick next to a mechanical gate adds nothing but a chance to be
  wrong.
- Human approval is the decision gate: CI says whether the change is correct according to the
  rules; review says whether it is the change we want.
- Never merge with CI red or with an open review finding.
- A description carries one attribution line, the one in the template. Tooling that opens or edits
  pull requests may append its own footer or a session link; a workflow
  ([.github/workflows/pr-description.yml](.github/workflows/pr-description.yml)) removes them every
  time a description is opened or edited, so nobody has to do it by hand.

## Quality gates

All of them run in CI ([.github/workflows/ci.yml](.github/workflows/ci.yml)) and can be run locally
with the same commands.

| Gate | Command | Threshold |
|---|---|---|
| Lint, including security (`S`) and cyclomatic complexity | `uv run ruff check .` | No findings; complexity ≤ 10 per function |
| Formatting | `uv run ruff format --check .` | No differences |
| Types | `uv run mypy` | Strict mode, no errors |
| Tests and coverage | `uv run pytest --cov` | All green; branch coverage ≥ 90 % |
| History in code | `uv run python -m tools.check_history` | No findings |
| EARS syntax | `uv run python -m tools.check_ears` | No findings |
| Traceability | `uv run python -m tools.check_traceability` | Every requirement with a test; every test with a marker |
| Markdown links | `uv run python -m tools.check_links` | No broken links |
| Spanish translations | `uv run python -m tools.check_translations` | Every document translated and up to date |
| Decision records | `uv run python -m tools.check_adrs` | Every ADR from 0008 on states its basis; every ADR agrees with the index |
| Mermaid diagrams | `npm ci` once, then `uv run python -m tools.check_mermaid` | Every diagram renders; fails if the renderer is missing |
| Tracked files that are ignored | `git ls-files --cached --ignored --exclude-standard` | Empty output |
| Commits | `uv run python -m tools.check_commits --base origin/main --branch <branch>` | No findings |
| Branch scope | `uv run python -m tools.check_scope --base origin/main --branch <branch>` | No findings |
| Dependencies | `pip-audit` over the locked dependencies | No known vulnerabilities |

Import contracts between modules are added in phase 1, when the architecture that defines them
exists.

## Requirements and traceability

Each scope has a `docs/requirements/<scope>.md` file. Each requirement takes one line:

```
- **CORE-001** When a gate rejects an attempt, the runner shall route to the state named by the gate.
```

- The identifier is the file name in upper case, a hyphen and three digits.
- The statement follows one of the five EARS templates, contains a single `shall` and uses no
  vague terms. The [ears-requirements](.claude/skills/ears-requirements/SKILL.md) skill explains
  how to write them.
- Every test file declares on its first non-empty line which requirements it proves:

  ```python
  # SDD-EARS: CORE-001 CORE-002
  ```

## Languages

Following [ADR-0005](docs/adr/0005-languages.md):

- **English** for code and everything around it: source, identifiers, comments, docstrings,
  commit messages, EARS requirements, module READMEs and the files agents read (`CLAUDE.md`,
  `.claude/skills/`, the pull request template).
- **English and Spanish** for human-facing documentation (README, CONTRIBUTING, roadmap, ADRs,
  architecture). English is the source; the Spanish version lives next to it as `<name>.es.md`.
- The first line of a Spanish version records the hash of the English text it translates. When the
  English file changes, `tools/check_translations.py` fails and prints the new header line to set
  once the translation has been reviewed.

## Comments and documentation

- **Code explains what it does and why, not how it got there.** No task identifiers, versions,
  dates or incident stories in comments or docstrings: that belongs in git and in the ADRs.
  `tools/check_history.py` rejects it.
- A comment that adds nothing the code does not already say should go.
- Every reference to a document must point to a file that exists in the repository.

## Definition of done for a scope

- EARS requirements written and reviewed.
- Every requirement with at least one test, red demonstrated before its implementation.
- Public interface documented in a short module README: what it does and how to use it.
- Every gate green, locally and in CI.
- An ADR for every decision with consequences.
- Closing report in the pull request description.
- Exit criteria of the phase updated in [docs/ROADMAP.md](docs/ROADMAP.md).
