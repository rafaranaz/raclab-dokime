# ADR-0027 · Memory has one layout, two storages and three scopes

**Status:** accepted

## Context

What survives between sessions must not depend on a summary written by a model, and in a team the
context of one story must not leak into another. No accepted standard for agent memory exists.

## Decision

- Memory is a directory of Markdown files, one per topic, each with a header: date, who approved
  it and the version of the code it was validated against.
- One layout, two storages: a local directory without git for a single developer, or the
  repository for a team. The implementation is the same.
- Three scopes: **project** (glossary, decisions, policy, pack), shared; **change** (the contract
  of a story, its examples and clarifications), in the directory and the branch of that change;
  **person** (the state of the run in progress, proposals not yet approved), local and never shared.
- Everything is saved at once. Approval changes the state of an item, not whether it is saved. A
  proposal lives in the local ledger until someone approves it; only then a file changes. The one
  exception is held-out content: once the split is done the ledger keeps its digest, not its
  content ([ADR-0014](0014-hidden-checks-are-held-out-approved-examples.md)).
- The state of the work comes from the ledger, not from a summary.
- The context file for agents is a small delimited block with what cannot be deduced from the code.

## Basis

Literature and reasoning. No form of memory wins everywhere, and stores curated by an agent can
fail badly ([study](https://www.alphaxiv.org/abs/2607.26637.md)); general repository overviews do
not improve results and cost 20 % more ([study](https://arxiv.org/abs/2602.11988)). One directory
per feature is how existing specification tools organise their files.

## Alternatives considered

- **Approved items only in the repository.** Stronger trace; it leaves the single developer
  without git out. The evidence labels the local case as self-attested instead.
- **A summary of the last session written by the model.** It loses things and carries errors on.

## Consequences

- In local storage, approvals have no independent trace.
- One file per glossary term and per decision, to avoid merge conflicts.
