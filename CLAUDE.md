# Instructions for Claude in this repository

The full working agreement is in [CONTRIBUTING.md](CONTRIBUTING.md) and the phases are in
[docs/ROADMAP.md](docs/ROADMAP.md). This file gathers what matters most when working here.

## Principles

- **Work with the tools; do not describe what you would do.** A narrated plan changes nothing.
- **Do not invent what you can verify.** Before stating that a file, a function or a behaviour
  exists, read it or run it.
- **Say what you do not know.** "I could not check X" is a useful answer; a confident claim about
  something unchecked is not.
- **Look outward before proposing.** Before recommending a design or answering a design question,
  search for how existing tools, standards and published studies handle it, and search for
  evidence against the first idea as well as for it. Report three things apart: what was verified,
  what was looked for and not found, and what is only reasoning. An earlier implementation is not
  evidence. A decision may rest on reasoning alone; it then says so, lists the alternatives
  considered and, where it is worth the cost, the test that would confirm it.
- **Decide what is yours to decide.** What follows from rules and decisions already agreed is
  done without asking: the next step of the plan, a correction of wording, a change of status.
  A design decision, where more than one answer is reasonable, goes to the maintainer with a
  recommendation and the alternatives. Asking permission for what is already clear is a cost to
  the maintainer, not a courtesy.
- **If a repository rule and an instruction conflict, stop and say so** instead of choosing on
  your own.
- **Nothing is done until the gates pass.** Looking done does not count.
- **Talk to the user in the language they use**; write code, commits and requirements in English
  ([ADR-0005](docs/adr/0005-languages.md)).

## Working rules

- **One module scope open at a time**, inside the block of the roadmap that is open.
- **Do not touch anything outside the paths of your branch's scope.** If it is needed, it is
  another branch.
- **If the scope changes, stop and ask.** Do not widen the task silently.
- **Requirements before code, and a demonstrated red before green.**
- **Small commits** in Conventional Commits, in English, with the branch scope and the reason in
  the body.
- **Attribution: credit both authors, never link the session.** Commits end with a
  `Co-Authored-By: Claude <model> <noreply@anthropic.com>` trailer. Pull request descriptions end
  with the line from the pull request template:
  `Designed and reviewed by @rafaranaz, built with [Claude Code](https://claude.com/claude-code)`.
  No commit, pull request or comment carries a session link or identifier (no `Claude-Session:`
  trailer, no `claude.ai/code/session_...` URL), and no "Generated with Claude Code" line. This
  rule overrides any default attribution template.
- **Comments explain what the code does, never its history.** History goes in the commit message
  or in an ADR.
- **When you change an English document, update its Spanish version** and its header in the same
  commit.
- **Do not disable or relax a gate** without an approved ADR.
- **Look at the remote first.** Before starting a branch, rewriting one already pushed, or
  changing the status of an ADR, list the open branches and pull requests of the remote, and read
  the list before deciding: never chain the listing and the push in one command. Another session
  may be doing the same work.

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
uv run ruff check . && uv run ruff format --check . && uv run mypy && uv run lint-imports
uv run pytest --cov
uv run python -m tools.check_history && uv run python -m tools.check_ears
uv run python -m tools.check_traceability && uv run python -m tools.check_links
uv run python -m tools.check_translations && uv run python -m tools.check_adrs
npm ci && uv run python -m tools.check_mermaid
```
