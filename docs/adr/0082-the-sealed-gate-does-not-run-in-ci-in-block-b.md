# ADR-0082 · The sealed gate does not run in CI in block B

**Status:** accepted

## Context

[ADR-0073](0073-the-key-of-the-hold-out-lives-outside-ci-until-b4.md) keeps the key of the sealed
batches out of CI until B4, and leaves to an ADR of B4 whether the gate `sealed-examples` runs in
CI. Its candidate is a workflow triggered by `workflow_run`, which runs with the file of the default
branch, with the key as a secret of an environment restricted to `main`, accepted only if the threat
model ([ADR-0010](0010-threat-model.md)) accepts the container of the sandbox as the only barrier
between the key and the code of the change. In B1 the maintainer left to the same ADR how the result
of a sealed run reaches a pull request: a status of the commit, `dokime/sealed-examples`, and a
comment; if the key entered CI, the gate would show in the summary of its job, as
[ADR-0070](0070-the-evidence-of-a-pull-request-goes-in-the-summary-of-its-job.md) does for the rest.

What block B measured: the hold-out turns the 8 false accepts of the cases that only it catches into
0 (B3e), in runs that the maintainer started on their machine, typing the passphrase, and that
`tests/corpus/held-out-run.toml` records. In CI the gate is not applicable, "the key is not here".

The gate runs the code of the change: it builds the tree of the change and observes the held-out
examples on it, in the sandbox. A job that holds the key and runs that code puts the second asset of
ADR-0010, the held-out content, behind the container alone; and hostile code aimed at the harness
itself, T5, is out of the scope of that threat model.

## Decision

- **The gate `sealed-examples` does not run in CI in block B.** The key stays out of CI with the
  mechanism of ADR-0073: the maintainer runs the sealed audit locally and types the passphrase, not
  on every pull request but before merging one that adds or changes a case or a contract with a
  sealed batch, and at the close of a block; in CI the gate stays not applicable, with the reason
  that the key is not here.
- **Nothing of a local sealed run is posted to the pull request**: no status of the commit and no
  comment. Its evidence stays in the directory `--out` of the run on the machine of the maintainer;
  for the corpus, `held-out-run.toml` records each run.
- **This is decided again before block C needs the gate without a person**, when an agent writes
  the change and nobody is there to type a passphrase.

## Basis

Verified in what GitHub publishes. The Security Lab of GitHub reports as a real vulnerability a
workflow triggered by `workflow_run` that runs, in a privileged context, what comes from a pull
request ([Preventing pwn requests](https://securitylab.github.com/research/github-actions-preventing-pwn-requests)),
and the documentation of GitHub asks to treat what comes from a pull request only as data
([securely using pull_request_target](https://docs.github.com/en/enterprise-cloud@latest/actions/reference/security/securely-using-pull_request_target)).
The sealed gate cannot treat the change as data: it runs it.

Reasoning, on that and on ADR-0010: the only barrier would be the container, which ADR-0010 does not
defend against code aimed at it (T5); and the value of the gate, measured in B3e, does not depend
on where it runs. On the status and the comment, reasoning as well: a status posted from the machine
of the maintainer needs a token with the right to write statuses there, and would say on GitHub what
no run of GitHub checked; the record in the repository is enough while one person runs the gate.

## Alternatives considered

- **`workflow_run` with the key as a secret of an environment restricted to `main`**, the
  candidate of ADR-0073. Discarded for block B: it accepts the container as the only barrier, which
  ADR-0010 does not.
- **A status of the commit posted from the local run.** Discarded: it needs a token with write
  rights on the machine of the maintainer, and shows as a check of GitHub what only that machine saw.
- **A comment on the pull request with the evidence of the local run.** Discarded for the same
  reason, and since the evidence of the gate tells which held-out id failed, which the roadmap
  leaves to decide before the evidence reaches the agent, in block C.

## Consequences

- A pull request shows nothing of the hold-out; whoever merges has to know that the maintainer ran
  the sealed audit, and the corpus keeps it in `held-out-run.toml`.
- The hold-out depends on one person and one machine. The batches of the corpus were sealed for one
  recipient only, though ADR-0073 asks for a second, so losing that identity would lose them. Two
  things lessen it: the maintainer keeps a copy of the identity, encrypted with its passphrase,
  away from the machine where the work is done; and the batches sealed from now on carry the second
  recipient that ADR-0073 asks for. The batches of today are not sealed again, since the files of a
  case do not change once it is added (CORPUS-030).
- Block C, where an agent writes the change, has to decide this again before it relies on the gate.
