# ADR-0071 · The harness that audits a pull request is that of its base

**Status:** proposed

## Context

A4 runs `audit` on each pull request of this repository, in a workflow run by `pull_request` with
the permission to read only
([ADR-0070](0070-the-evidence-of-a-pull-request-goes-in-the-summary-of-its-job.md)). The contract and
the pack of an audit already come from the base of the change and never from the patch
([ADR-0067](0067-a-person-approves-the-contract-before-a-change-is-audited-against-it.md),
INTERFACES-075). In this repository the harness is the project: a pull request that changes dokime
changes the program that audits it. By default the workflow checks out the merge commit of the pull
request, so such a pull request would be audited by its own code, and could give itself `PASS`.

The session that reviews the work found the problem; the decision is the maintainer's.

## Decision

**The rule.** The code that judges a change never comes from that change. The harness that audits a
pull request is that of its base, as its contract and its pack are.

**The mechanism in A4, in attended use.**

- **The workflow checks out `github.event.pull_request.base.sha` into a directory of its own**,
  installs dokime there and runs it from there.
- **It audits the patch of the pull request**, the difference between its base and its head, against
  a checkout of the project.
- **The commit of the harness in the evidence is that of the base**
  ([ADR-0068](0068-the-harness-is-named-by-its-version-and-its-commit.md)), and the summary of the job
  shows it, so the maintainer can see that it is the base of the pull request.

**The limit.** The workflow file still comes from the pull request, since the event is
`pull_request`: a pull request could change it so that it runs its own dokime, or none. Without
`pull_request_target`, which ADR-0070 refused, this has no mechanism; it holds by discipline, since
the pull requests are opened with the account of the maintainer, and the maintainer checks in the
summary that the commit of the harness is the base before merging.

## Basis

Verified in the documentation of GitHub: "By default, `actions/checkout` in a `pull_request` workflow
also checks out the pull request's merge commit", while for `pull_request_target` "the workflow file
itself still comes from the default branch"
([securely using pull_request_target](https://docs.github.com/en/actions/reference/security/securely-using-pull_request_target)).

Read with `gh`, in tools of others that check pull requests with code that a pull request could
change:

- [TrianaLab/aval, issue #134](https://github.com/TrianaLab/aval/issues/134), closed: the CI of a pull request should load its trust policy from the
  base branch, since otherwise "a green PR check would be evidence the PR authored itself".
- [microsoft-365-agents-toolkit, pull request #16697](https://github.com/OfficeDev/microsoft-365-agents-toolkit/pull/16697), merged: "Check out the evaluation harness from
  the exact PR base SHA", with the content of the pull request overlaid as data; it runs on
  `pull_request_target` with an environment that needs an approval.
- [electrum, pull request #11076](https://github.com/spesmilo/electrum/pull/11076), closed without merging: the security review checks out the trusted
  source from `pull_request.base.sha` and takes the pull request only as data of git.

Reasoning, without a test: that the harness of the base, named by its commit in the summary, lets
the maintainer see before merging that the change did not judge itself. The test is the first pull
request of A4 that changes dokime and carries its evidence.

## Alternatives considered

- **Run the harness of the pull request itself.** It is simpler, but the self-audit loses its sense
  exactly in the pull requests that change dokime.
- **`pull_request_target`, with the workflow from the base.** It would close the limit, but the job
  would get a token that can write while it runs the code of the change, which ADR-0070 refused.
- **Install a published version of dokime.** Nothing is published until someone outside uses it
  (ADR-0068).

## Consequences

- A pull request that changes dokime is audited by the dokime of its base: its new checks apply only
  from the next pull request after its merge, the cost that microsoft-365-agents-toolkit states too:
  "Evaluation harness changes take effect after they are merged into the base branch".
- The workflow checks out twice: the base, for the harness, and the project with the pull request.
- In A4 the rule holds for the workflow file by discipline, and the summary of the job is what the
  maintainer checks.
