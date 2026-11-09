# ADR-0005 · English for code, bilingual documentation and a bilingual product

**Status:** accepted

## Context

The team works in Spanish. The harness generates and parses EARS requirements with the canonical
English keywords (`When`, `While`, `If ... then`, `Where`, `shall`), and agents working on code
perform better and cost less with English identifiers, comments and prompts. In `dokime` both
languages coexisted without a rule, which forced later translations of skills and validators.

The people who use the harness should be able to work with it in Spanish or in English.

## Decision

- **Code and everything around it is in English**: source code, identifiers, comments,
  docstrings, commit messages, EARS requirements, module READMEs, and the files agents read
  (`CLAUDE.md`, `.claude/skills/`, the pull request template).
- **Human-facing documentation is in English and Spanish**: README, CONTRIBUTING, roadmap, ADRs
  and architecture. English is the source. The Spanish version lives next to it as `<name>.es.md`
  and records the hash of the English text it was translated from; `tools/check_translations.py`
  fails CI when a document changes without its translation being reviewed.
- **The product lets the user choose Spanish or English** for everything they read or write:
  interviews, the request, clarifying questions, approval gates and reports. Internal artifacts and
  model prompts stay in English. How the boundary is implemented (translating at the edge or
  conversing directly in the chosen language) is decided in the architecture phase, in its own
  ADR.

## Alternatives considered

- **Documentation in Spanish only.** Leaves out readers who do not speak Spanish and splits the
  repository into two languages without a rule for which goes where.
- **Everything in English, product included.** Simpler and cheaper, but it does not meet the goal
  of letting Spanish-speaking users work in their language.
- **Spanish as the source of the documentation.** The documentation describes code that is in
  English and is read by agents that work best in English; keeping English as the source avoids
  translating in two directions.

## Consequences

- Every documentation change has to be made twice. The translation check makes that cost visible
  and prevents the versions from silently drifting apart.
- Requirement files and module READMEs are English only, because they are part of the code.
- The bilingual product adds a requirement to the user-facing modules (interviews, gates, reports)
  that the architecture must account for from the start.
