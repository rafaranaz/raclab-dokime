# ADR-0067 · A person approves the contract before a change is audited against it

**Status:** proposed

## Context

In A3 the contract of an audit comes from the base commit, or is given to `audit` from outside the
patch, and never from the patch, and `.dokime/` is protected without exception (VERIFY-024): a
contract that a patch brings cannot be told from one that its agent wrote. The roadmap left for
before A4 how an audit of a pull request that brings its own contract fits that rule. A4 audits the
pull requests of this repository in CI, so each of them needs a contract that a person approved. The
signed approvals are of block E.

In A4 the pull requests of this repository are opened with the account of the maintainer, by the
maintainer or by an agent working for them, so GitHub cannot tell one from the other.

## Decision

**The rule.** A contract is approved by a person before a change is audited against it, and the
agent that makes the change can neither touch the contract nor approve it. The rule holds in every
mode of use; what changes from one mode to another is the mechanism that meets it.

**The mechanism in A4, in attended use.**

- **Two pull requests.** The contract enters `main` in a pull request of its own, at
  `.dokime/changes/<story>/contract.yaml`, and the merge of that pull request by the maintainer is
  its approval. The change comes in another pull request, which is audited against the contract of
  its base. A change that touches `.dokime/` fails the gate `protected-paths`, as in A3.
- **The story comes from the name of the branch** of the change, `<type>/<scope>-<description>`:
  the story is the description. It is not taken from the description of the pull request, which
  whoever opens it writes.
- **The summary of the job shows the story and the digest of the contract** that the audit used,
  and the maintainer checks them before merging the pull request of the change.

**The limit.** In A4 the pull requests are opened with the account of the maintainer, so the merge
as approval and the story from the branch hold by discipline, not because GitHub prevents anything
else: an agent with that account could merge a contract or name another branch. The protection is
that the maintainer checks the story and the digest of the contract before merging the code. When
the agent has an identity of its own, the same rule is met by a mechanism, not by discipline.

**Mechanisms the rule admits later**, without rewriting it:

- a required review by the code owners of `.dokime/**`, once the pull requests are opened by an
  identity other than the maintainer's;
- the signed approval of block E, with the contract whose digest matches it;
- in semi-attended or unattended use, which is not decided: a reviewing agent other than the one
  that made the change, without the context of its development and preferably of another family of
  models, under a policy approved by a person.

## Basis

Verified in the documentation of GitHub:

- A required review by code owners makes at least one code owner approve a pull request that
  changes the files they own, and the file `CODEOWNERS` is read from the base branch of the pull
  request
  ([about code owners](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners)).
- A workflow run by `pull_request` from a fork gets a token that can only read, and one run by
  `pull_request_target` gets one that can write
  ([the token of GitHub](https://docs.github.com/fr/enterprise-server@3.13/actions/reference/github_token-reference)).

Looked for and not found: the page of GitHub that says that the author of a pull request cannot
approve it. Guides of others say so
([Graphite](https://graphite.com/guides/pull-request-approval-permissions-rules-github)); it does
not matter in A4, where one account opens and merges.

Reasoning, without a test: that a story taken from the branch, shown with the digest of its
contract in the summary of the job, is enough for the maintainer to see that the change was audited
against the contract they approved. The test is the first pull request of A4 that carries its
evidence.

## Alternatives considered

- **The contract in the same pull request as the change.** The agent could write the judge of its
  own change; that is what A3 refused.
- **Only the contract whose digest matches a signed approval**, the candidate of the roadmap. It
  needs the signatures of block E.
- **The story from the description of the pull request.** Whoever opens the pull request writes it,
  and could name another contract already approved and easier to meet.
- **The contract has to have entered `main` after the base of the branch was taken.** It would keep
  an old contract from being reused, but the audit needs the contract in its base, so the condition
  has no single reading; the check of the story and the digest by the maintainer covers the same
  risk in A4.

## Consequences

- Each change with a contract is two pull requests, and the contract is merged first.
- In A4 the rule holds by the discipline of one person, and the evidence says `self-attested`.
- The maintainer reads the story and the digest of the contract in the summary of the job before
  each merge of code.
- A pull request whose branch names no story with a contract in its base is not audited against a
  contract; how the workflow says so is a requirement of the workflow.
