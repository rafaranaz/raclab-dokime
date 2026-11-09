## What changes and why

<!-- One or two sentences. The detail of each step is in the commits. -->

## Scope

- Branch: `type/scope-description`
- Affected requirements: <!-- e.g. CORE-001, CORE-004, or "none" -->

## For the reviewer

CI already enforces the mechanical rules (tests, coverage, traceability, translations, commits,
scope), and the merge button stays disabled until it passes. These are the points only a
review can judge:

- [ ] The requirements express the agreed intent, not just a valid syntax
- [ ] Every decision with consequences has its ADR, new or superseding another
- [ ] If it closes a scope, it includes the closing report (see `.claude/skills/close-scope`)
