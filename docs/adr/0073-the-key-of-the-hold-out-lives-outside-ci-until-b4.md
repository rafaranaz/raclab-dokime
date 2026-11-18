# ADR-0073 · The key of the hold-out lives outside CI until B4

**Status:** proposed

## Context

The held-out examples of a contract are encrypted for a list of recipients
([ADR-0072](0072-the-sealed-store-is-encrypted-with-age-for-a-list-of-recipients.md)). The gate
`sealed-examples` needs a private key to decrypt them and has to run the code of the change to
observe it with them. The architecture says that "the sealed run happens only where the key is", and
that elsewhere the gate is not applicable and the evidence says so
([states and flows](../architecture/04-states-and-flows.md)).

[ADR-0020](0020-agent-isolation-is-optional-adoption-is-a-ladder.md) put the key there: "The key of
the sealed batches lives only in CI. A developer's machine cannot decrypt them." It let a single
developer without CI keep the key locally, with held-out content "decrypted only in memory, never
written to disk", stated in the evidence "as best effort", and with the evidence recording the
barrier between where the examples are in clear and the agent: "another machine, the wrapper,
another system user, or none".

In this repository CI is not a safe place for the key: the audit of a pull request runs in a
workflow whose file comes from the pull request, so a pull request can change what that workflow
does ([ADR-0071](0071-the-harness-that-audits-a-pull-request-is-that-of-its-base.md)). And in block
B the change is written by an agent on the same machine where the key would then be.

The strategic review at the close of block A compared the options; the maintainer approved this
recommendation. The session that reviews the work researched it first and found that it had to
amend ADR-0020 and cover the agent on the same machine; the decision is the maintainer's.

## Decision

This amends ADR-0020: the key of the sealed batches does not live in CI until B4 decides otherwise,
and the conditions that ADR-0020 set for a developer without CI become the rule.

**The rule.** A key that decrypts held-out content is never within reach of a workflow that a pull
request can change, of the agent that writes the change, nor of the code being judged.

**The mechanism in B1 to B3, in attended use.**

- **The identity is an age identity kept encrypted with a passphrase**: an age file encrypted with a
  passphrase, which the binary `age` also reads as an identity file, in the state directory of the
  harness, outside the working tree. A second recipient, chosen by the maintainer, keeps its own
  identity apart, so that losing one does not lose the sealed batches.
- **The maintainer types the passphrase at the sealed run.** dokime decrypts the identity and the
  sealed batch only in memory, never on disk, and the evidence states it as best effort.
- **The identity never enters the sandbox** where the code being judged runs.
- **The evidence records the barrier between the key and the agent**: another machine, the wrapper,
  another system user, a passphrase, or none. A passphrase is added to the list of ADR-0020.
- **The sealed run is made locally**, before the merge. In CI the gate `sealed-examples` is not
  applicable, with the reason that the key is not there.
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

Verified in age and pyrage on 2026-11-18:

- The README of [age](https://github.com/FiloSottile/age): "If an identity file passed to `-i` is a
  passphrase encrypted age file, it will be automatically decrypted"; and "Passphrase-protected
  identity files are not necessary for most use cases, where access to the encrypted identity file
  implies access to the whole system."
- pyrage 1.4.0 has `passphrase.decrypt(ciphertext, passphrase)` and `x25519.Identity.from_str`, so an
  identity encrypted with a passphrase can be decrypted in memory. Its `ssh.Identity.from_buffer`
  takes no passphrase in 1.4.0: the support of encrypted SSH keys was merged on September 27, 2026
  ([#159](https://github.com/woodruffw/pyrage/pull/159)), after that version, and is not released.

Looked for and not found: a sentence of the documentation of GitHub that says whether the pull
requests from branches of the same repository receive its secrets. The first sentence above makes
it unnecessary: whoever can push a branch can write a workflow that reads them.

Reasoning, without a test:

- That the sealed run needs both the key and running the code of the change, which is exactly what
  the pattern of Security Lab keeps apart, so any run of it in CI joins the two on one machine with
  the container as the only barrier. The test is the threat model of B4.
- That a passphrase keeps the key from an agent that reads the file, but not from an agent that
  runs as the same user and changes what will run later, the shell, the installation of the
  harness or a hook, to capture the passphrase: the limit that the README of age states. Another
  system user, or another machine, removes it. The test, in B1: a sealed run without the
  passphrase cannot decrypt, and the evidence names the barrier used.

## Alternatives considered

- **The identity owned by another system user**, with the sealed run made as that user. The agent
  can neither read the identity nor change what that user runs, which closes the limit of the
  passphrase; it costs a user to set up and a container engine that runs as that user.
- **Another machine** for the sealed run. The strongest barrier, and the most work for each pull
  request.
- **An SSH key encrypted with a passphrase.** It reuses a key the maintainer already has, but pyrage
  does not support it in a released version.
- **A key file in clear in the state directory.** The agent that writes the change can read it.
- **The key as a secret of the repository, in the workflow of the pull request.** A pull request can
  change that workflow and read the key.
- **The sealed run in CI from B1**, with `workflow_run`, an environment restricted to `main` and
  required reviewers. The reviewers add a human gate, but the code of the change still runs next to
  the key, with the container as the only barrier; it is the pattern that Security Lab advises
  against, and it is weighed in B4 with the threat model instead of assumed now.
- **A hardware key through a plugin of age.** Not examined.

## Consequences

- ADR-0020 is amended: in this repository the key does not live in CI, and its consequence that
  "sealed results arrive when the change is pushed" no longer holds: they arrive when the maintainer
  makes the sealed run, before the merge.
- Every pull request with held-out examples needs a manual step on the machine of the maintainer,
  who types the passphrase, and the evidence of CI does not cover the sealed examples; how the
  result of the local run reaches the pull request is decided when `verify` builds the gate.
- The evidence of a sealed run carries two things it does not carry today, that the decryption was
  best effort and the barrier used; the predicate gets them when `evidence` is touched in B1.
- The barrier of a passphrase is weaker than another system user against an agent that runs as the
  same user; the evidence names it, so a reader can weigh it.
- The example of evidence in the [architecture](../architecture/03-data-and-evidence.md) gives the
  reason "the key lives only in CI", the opposite of this decision; it is corrected in the scope
  `arch` when block B opens.
