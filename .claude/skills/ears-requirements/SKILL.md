---
name: ears-requirements
description: Write or review EARS requirements in docs/requirements/. Use when opening a scope, before writing any test or code.
---

# EARS requirements

EARS exists to remove ambiguity from prose requirements. Every requirement uses one of these five
templates, and no other:

| Type | Template | When |
|---|---|---|
| Ubiquitous | `The <component> shall <response>.` | Always true, no trigger |
| Event-driven | `When <trigger>, the <component> shall <response>.` | Reaction to something that happens |
| State-driven | `While <state>, the <component> shall <response>.` | In force during a state |
| Unwanted behaviour | `If <unwanted condition>, then the <component> shall <response>.` | Errors and edge cases |
| Optional feature | `Where <feature is present>, the <component> shall <response>.` | Depends on configuration |

State and event can be combined: `While <state>, when <trigger>, the <component> shall <response>.`

## Format in this repository

In `docs/requirements/<scope>.md`, one requirement per line, in English:

```
- **GRAPH-004** If a reference matches more than one symbol, then the resolver shall emit no edge with confidence 1.0.
```

- Identifier: the scope in upper case, a hyphen and three digits. Retired identifiers are not
  reused.
- Requirements can be grouped under headings.

## Rules that make them worth something

- **One requirement, one verifiable behaviour.** If you need "and" to join two different
  responses, they are two requirements. `tools/check_ears.py` rejects more than one `shall`.
- **The response is observable from outside.** "Shall validate correctly" is not verifiable;
  "shall reject the request with an error naming the field and leave the state unchanged" is.
- **Unwanted cases are not optional.** A requirement without its `If ... then` leaves the error
  path unspecified, which is exactly where defects slip in.
- **No quality adverbs without a metric.** "Fast", "robust", "efficient" do not belong; if there is
  a limit, write it with its number. The check rejects a list of vague terms.
- **Every requirement has at least one test** that declares it in its `# SDD-EARS:` marker.

## Before accepting the requirements

- Read them as the implementer: could you write the test without asking anything?
- Look for the error case of every event and the boundary value of every threshold.
- Run them through `uv run python -m tools.check_ears`.
