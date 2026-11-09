---
name: close-scope
description: Close the work on a scope before asking for its merge. Use when the scope is believed to be finished, to check it and write the closing report.
---

# Close a scope

A scope is not finished because it looks finished, but when it meets its definition of done
([CONTRIBUTING.md](../../../CONTRIBUTING.md#definition-of-done-for-a-scope)).

## 1. Run every gate locally

```bash
uv sync --locked
uv run ruff check .
uv run ruff format --check .
uv run mypy
uv run pytest --cov
uv run python -m tools.check_history
uv run python -m tools.check_ears
uv run python -m tools.check_traceability
uv run python -m tools.check_links
uv run python -m tools.check_translations
npm ci && uv run python -m tools.check_mermaid
git ls-files --cached --ignored --exclude-standard
uv run python -m tools.check_commits --base origin/main --branch "$(git branch --show-current)"
uv run python -m tools.check_scope --base origin/main --branch "$(git branch --show-current)"
```

If any of them fails, the scope is not closed. Fix it with the `tdd` or `debug` skills; do not
disable it or lower its threshold without an ADR.

## 2. Check what CI cannot check

- Does every requirement express the agreed intent, and not just pass the syntax check?
- Do the tests prove behaviour and not internal details?
- Does the module README explain what it does and how to use it, without telling its history?
- Were there decisions with consequences? Each one needs its ADR.

## 3. Write the closing report in the pull request description

- **What the module does**, in two or three sentences.
- **Requirements**: how many, and the list of identifiers.
- **Gates**: the result of each one and the module's coverage.
- **Known limitations**, stated plainly: what it does not do or what could not be checked.
- **ADRs** added or superseded.

## 4. Update the roadmap

Tick the exit criteria met in `docs/ROADMAP.md` and its Spanish version. The next scope does not
open until this pull request is merged.
