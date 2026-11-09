# Instructions for Claude in this repository

The full working agreement is in [CONTRIBUTING.md](CONTRIBUTING.md) and the phases are in
[docs/ROADMAP.md](docs/ROADMAP.md). This file gathers what matters most when working here.

## Principles

- **Work with the tools; do not describe what you would do.** A narrated plan changes nothing.
- **Do not invent what you can verify.** Before stating that a file, a function or a behaviour
  exists, read it or run it.
- **Say what you do not know.** "I could not check X" is a useful answer; a confident claim about
  something unchecked is not.
- **If a repository rule and an instruction conflict, stop and say so** instead of choosing on
  your own.
- **Nothing is done until the gates pass.** Looking done does not count.
- **Talk to the user in the language they use**; write code, commits and requirements in English
  ([ADR-0005](docs/adr/0005-languages.md)).

## Working rules

- **One module scope open at a time**, and only if the current phase of the roadmap allows it.
- **Do not touch anything outside the paths of your branch's scope.** If it is needed, it is
  another branch.
- **If the scope changes, stop and ask.** Do not widen the task silently.
- **Requirements before code, and a demonstrated red before green.**
- **Small commits** in Conventional Commits, in English, with the branch scope and the reason in
  the body.
- **Comments explain what the code does, never its history.** History goes in the commit message
  or in an ADR.
- **When you change an English document, update its Spanish version** and its header in the same
  commit.
- **Do not disable or relax a gate** without an approved ADR.

## Skills

| Skill | When |
|---|---|
| `open-scope` | Before writing code for a new scope |
| `ears-requirements` | When writing or reviewing requirements |
| `tdd` | When implementing any behaviour |
| `debug` | On a failure, before changing code |
| `adr` | When taking a decision with consequences |
| `close-scope` | Before asking for a scope to be merged |

## Gates locally

```bash
uv sync --locked
uv run ruff check . && uv run ruff format --check . && uv run mypy && uv run pytest --cov
uv run python -m tools.check_history && uv run python -m tools.check_ears
uv run python -m tools.check_traceability && uv run python -m tools.check_links
uv run python -m tools.check_translations
```
