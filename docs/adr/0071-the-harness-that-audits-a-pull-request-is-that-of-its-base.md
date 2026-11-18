# ADR-0071 · The harness that audits a pull request is that of its base

**Status:** accepted

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
  shows it.

**The limit.** The workflow file still comes from the pull request, since the event is
`pull_request`: a pull request could change it so that it runs its own dokime, or none, and a
workflow it changed can write in the summary of the job whatever it wants, a commit of the base and
`PASS` included. So the summary cannot show that the workflow was not changed. What the maintainer
checks before merging is that the pull request changes nothing under `.github/workflows/`; only
then is the summary to be trusted. Without `pull_request_target` this has no mechanism; it holds by
discipline, since the pull requests are opened with the account of the maintainer.

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

Read in the same page of GitHub, and in the account of an incident by SafeDep, on why the workflow
does not run on `pull_request_target`:

- The job "receives the base repository's GITHUB_TOKEN and access to repository and organization
  secrets".
- The cache is outside the permissions of the token. In the incident of TanStack, on May 11, 2026,
  a workflow on `pull_request_target` wrote a poisoned cache into the scope of the default branch,
  and "the job's `permissions` block controlled API access but had no effect on cache writes"
  ([SafeDep](https://safedep.io/tanstack-github-actions-cache-poisoning/)). The page of GitHub now says that such a workflow has read-only access
  to the cache of the default branch, unless it declares a `cache-mode` that writes, which
  "reintroduces the cache-poisoning risk this restriction is designed to prevent": the protection is a default that a workflow can turn off.
- GitHub "provides a default event policy that blocks the `pull_request_target` event in public
  repositories", in evaluation now and enforced from December 2, 2026; and `actions/checkout` refuses
  the head of a pull request from a fork on that event unless `allow-unsafe-pr-checkout` is set.

Reasoning, without a test: that the harness of the base, with a pull request that changes no
workflow, lets the maintainer see before merging that the change did not judge itself. The test is the first pull
request of A4 that changes dokime and carries its evidence.

## Alternatives considered

- **Run the harness of the pull request itself.** It is simpler, but the self-audit loses its sense
  exactly in the pull requests that change dokime.
- **`pull_request_target`, with the workflow from the base.** It would close the limit, but the job
  would run the code of the change with the secrets of the repository, and with the cache of the
  default branch, which the permissions of the token do not bound and whose protection a workflow
  can turn off; GitHub blocks the event by default in public repositories, and `actions/checkout`
  refuses there the code of a pull request from a fork (see the basis).
- **Install a published version of dokime.** Nothing is published until someone outside uses it
  (ADR-0068).

## Consequences

- A pull request that changes dokime is audited by the dokime of its base: its new checks apply only
  from the next pull request after its merge, the cost that microsoft-365-agents-toolkit states too:
  "Evaluation harness changes take effect after they are merged into the base branch".
- The workflow checks out twice: the base, for the harness, and the project with the pull request.
- In A4 the rule holds for the workflow file by discipline: before merging, the maintainer checks that
  the pull request changes nothing under `.github/workflows/`, and only then reads the summary of
  the job as trustworthy.
