# ADR-0073 · The key of the hold-out lives outside CI until B4

**Status:** proposed

## Context

The held-out examples of a contract are encrypted for a list of recipients
([ADR-0072](0072-the-sealed-store-is-encrypted-with-age-for-a-list-of-recipients.md)). The gate
`sealed-examples` needs a private key to decrypt them and has to run the code of the change to
observe it with them. The architecture already says that "the sealed run happens only where the key
is", and that elsewhere the gate is not applicable and the evidence says so
([states and flows](../architecture/04-states-and-flows.md)). It does not say where the key is.

In this repository the audit of a pull request runs in a workflow whose file comes from the pull
request, so a pull request can change what that workflow does
([ADR-0071](0071-the-harness-that-audits-a-pull-request-is-that-of-its-base.md)).

The strategic review at the close of block A compared the options; the maintainer approved this
recommendation. The session that reviews the work researched it first; the decision is the
maintainer's.

## Decision

**The rule.** A key that decrypts held-out content is never within reach of a workflow that a pull
request can change.

**The mechanism in B1 to B3, in attended use.**

- **The key lives on the machine of the maintainer**, in the state directory of the harness,
  outside the working tree, as the
  [layout of memory](../architecture/03-data-and-evidence.md) foresees for "the key when it is
  local". A second recipient, chosen by the maintainer, keeps its own key apart, so that losing one
  key does not lose the sealed batches.
- **The sealed run is made locally**, before the merge, on the machine that has the key.
- **In CI the gate `sealed-examples` is not applicable**, with the reason that the key is not
  there.
- **The key is never a secret of the repository.**
- **Running the sealed gate in CI is decided apart, in B4**, with an ADR of its own. The candidate is
  a workflow triggered by `workflow_run`, which runs with the file of the default branch, and the key
  as a secret of an environment restricted to `main`, accepted only if the threat model
  ([ADR-0010](0010-threat-model.md)) accepts the container of the sandbox as the only barrier
  between the key and the code of the change.

## Basis

Verified in the documentation of GitHub on 2026-11-18:

- "Any user with write access to your repository has read access to all secrets configured in your
  repository" ([secure use](https://docs.github.com/en/actions/reference/security/secure-use)); and,
  "with the exception of `GITHUB_TOKEN`, secrets are not passed to the runner when a workflow is
  triggered from a forked repository"
  ([using secrets](https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-secrets)).
- `workflow_run` "will only trigger a workflow run if the workflow file exists on the default
  branch", with `GITHUB_SHA` the "Last commit on default branch" and `GITHUB_REF` the "Default
  branch"; and "Running untrusted code on the `workflow_run` trigger may lead to security
  vulnerabilities"
  ([events that trigger workflows](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows)).
- The rule of branches of an environment "is matched against the `GITHUB_REF` of the workflow run",
  and a rule for `refs/pull/*/merge` would let `pull_request` events use it; with required
  reviewers, a job cannot access the secrets of the environment until one approves it; on GitHub
  Free, the secrets of an environment and its required reviewers exist only in public repositories
  ([deployments and environments](https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments)).
  This repository is public.
- GitHub Security Lab puts untrusted code in a `pull_request` workflow, "isolated in an unprivileged
  environment", and gives the secrets to a separate `workflow_run` workflow that acts on its
  results, warning that "Artifacts resulting from untrusted PR data are themselves untrusted"
  ([preventing pwn requests](https://securitylab.github.com/resources/github-actions-preventing-pwn-requests/)).

Looked for and not found: a sentence of the documentation of GitHub that says whether the pull
requests from branches of the same repository receive its secrets. The first sentence above makes
it unnecessary: whoever can push a branch can write a workflow that reads them.

Reasoning, without a test: that the sealed run needs both the key and running the code of the
change, which is exactly what the pattern of Security Lab keeps apart, so any run of it in CI joins
the two on one machine with the container as the only barrier. The test is the threat model of
B4.

## Alternatives considered

- **The key as a secret of the repository, in the workflow of the pull request.** A pull request can
  change that workflow and read the key.
- **The sealed run in CI from B1**, with `workflow_run`, an environment restricted to `main` and
  required reviewers. The reviewers add a human gate, but the code of the change still runs next to
  the key, with the container as the only barrier; it is the pattern that Security Lab advises
  against, and it is weighed in B4 with the threat model instead of assumed now.
- **An environment open to `refs/pull/*/merge`.** It gives the key to the workflow that the pull
  request can change.

## Consequences

- Every pull request with held-out examples needs a manual step on the machine of the maintainer,
  and the evidence of CI does not cover the sealed examples; how the result of the local run
  reaches the pull request is decided when `verify` builds the gate.
- The sealed run depends on the machine of the maintainer being available; the second recipient
  covers the loss of the key, not the absence of the person.
- The example of evidence in the [architecture](../architecture/03-data-and-evidence.md) gives the
  reason "the key lives only in CI", the opposite of this decision; it is corrected in the scope
  `arch` when block B opens.
