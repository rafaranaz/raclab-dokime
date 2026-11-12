# ADR-0042 · Memory persists on local disk or in its own git repository

**Status:** accepted

## Context

[ADR-0027](0027-memory-has-one-layout-and-three-scopes.md) says that memory has one layout and two
storages, "a local directory without git for a single developer, or the repository for a team".
The decision it recorded was "the same structure in local and in git": memory is a store of its
own, kept as a plain directory or as a git repository. Written as "the repository", it was then
read as the repository of the verified project: the document of data put memory in `.dokime/`
inside that project, and [ADR-0041](0041-the-environment-of-a-verified-project-is-a-dockerfile.md)
put the pack there. This record states the two ways memory persists and who uses each, so that it
cannot be read that way again.

## Decision

- **Memory is a store of its own.** It is never inside the repository of the verified project,
  and that repository holds nothing of the harness.
- **Two modes of persistence, chosen by whoever uses the harness:**

| Mode | Where memory is | Who uses it |
|---|---|---|
| Local disk | A directory on the machine, without git | One person who uses the harness alone and chooses to keep memory local |
| Git repository | A git repository of its own, apart from the repository of the verified project | One person, or a team of more than one, who choose git in order to share the memory of the project |

- **The layout is the same in both modes**, the one of ADR-0027.
- **What memory holds** is what the three scopes of ADR-0027 hold: of the project, the glossary,
  the decisions, the policy, the pack, the flow and the list of allowed signers; of each change,
  its contract, its examples, its clarifications, its approval and its sealed batch; of the person,
  the state of the work in progress and the proposals not yet approved.
- **The scope of the person stays on the machine in both modes.** It is not pushed to the git
  repository of memory.
- **The pack** of a verified project is in its memory, in the scope of the project, or it is a
  file given to the command. This replaces the place that ADR-0041 gave it.

## Basis

A decision of the maintainer, taken before the first records were written and restated now. The
earlier wording is in the list of agreed decisions: "the same structure in local and in git". The
conversation in which it was taken is not available, so its exact words cannot be quoted.

Reasoning: the verified project may belong to someone else, as the repositories of the corpus do,
and the harness does not change them; and memory that is shared among projects of the same person
or team needs a home that is not any one of them. From memory, not checked: tools that keep
specifications usually put their files inside the repository of the project, which this decision
does not do. No test.

## Alternatives considered

- **Memory inside the repository of the verified project.** What the records said by mistake. It
  puts files of the harness in a repository that may not be ours, and it makes public what a
  person or a team may want private.
- **Only what is signed inside the project, the rest outside.** It splits one layout in two
  places, and ADR-0027 already counts the contract and the pack as memory.

## Consequences

- An audit that runs in a pipeline has to be given the memory: a checkout of its git repository,
  or the files of the change.
- The memory of a public project can be private. The evidence then cites a contract by its digest
  that not everyone can read.
- A change lives in two places that go together: the branch in the repository of the project and
  the directory of the change in memory, joined by the id of the story.
- On local disk, approvals have no independent trace, as ADR-0027 already says.
