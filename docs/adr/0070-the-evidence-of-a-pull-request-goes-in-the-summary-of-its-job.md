# ADR-0070 · The evidence of a pull request goes in the summary of its job and in an artifact

**Status:** proposed

## Context

A4 runs `audit` on each pull request of this repository and has to show its result to the
maintainer before the merge. The code of the change runs in that job, inside the containers of the
verification, and the messages of the findings quote text that dokime did not write
([ADR-0064](0064-the-evidence-of-a3-is-an-unsigned-statement-with-a-closed-predicate.md)). The
evidence is not signed until block E.

## Decision

**The rule.** The evidence of an audit in CI reaches the person who merges, and the workflow that
runs the code of the change holds no right to write in the repository.

**The mechanism in A4.**

- **The workflow runs on `pull_request`**, with the permission `contents: read` only, and never on
  `pull_request_target`.
- **The summary of the job** shows only the fields that dokime fixes: the verdict, the story, the
  digest of the contract, each gate with its status and its verdict, the codes of the findings, and
  the digest of the evidence. The messages, which may quote the code of the change, are not shown
  there.
- **The evidence file and the ledger** are uploaded as an artifact of the job.
- **Nothing is written in the pull request.** A comment, when it is wanted, is a second workflow
  run by `workflow_run`, with the permission to write and without the code of the change.

## Basis

Verified in the documentation of GitHub: a workflow run by `pull_request` from a fork gets a token
that can only read, and one run by `pull_request_target` gets a token that can write, even for a fork
([the token of GitHub](https://docs.github.com/fr/enterprise-server@3.13/actions/reference/github_token-reference)).
The writings on its risk advise running the code of a fork only on `pull_request`
([SonarSource](https://rules.sonarsource.com/githubactions/RSPEC-7631)).

The session that reviews the work read in the documentation of GitHub that an artifact is kept 90
days by default.

Reasoning, without a test: the fields of the summary are names, verdicts, codes and digests that the
reader of the evidence checks against their patterns, so they need no escaping, and a message that
quotes the code of the change stays in the artifact. The test is the first pull request of A4 that
carries its evidence.

## Alternatives considered

- **A comment in the pull request.** It needs the permission to write. Done safely, it is a second
  workflow, which is kept for when a comment is wanted.
- **An attestation with `actions/attest`**, which accepts a predicate type of our own. It signs with
  the identity of the workflow, which is the independence `ci-verified` and the signatures of
  block E.
- **A check run with annotations.** It needs the permission to write `checks`.

## Consequences

- The maintainer opens the job to see the result, and the artifact to read the whole evidence.
- **The limit: the artifacts expire**, after 90 days by default in GitHub, so the evidence of a pull
  request is not permanent in A4. Keeping it for good is the evidence store of the architecture,
  which comes with block E.
- No job of this repository that runs the code of a change can write in it.
