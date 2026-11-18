# The corpus

The harness is measured on a corpus with known verdicts
([ADR-0030](../../docs/adr/0030-the-harness-is-measured-on-a-corpus-with-known-verdicts.md)). Its
requirements are in [corpus.md](../../docs/requirements/corpus.md).

## The projects

Each directory is a project: its `pack.yaml`, its `Dockerfile`, its `source.toml`, which names the
repository and the commit, and its `cases/`. The code of a project is not copied. The self-check of
each pack runs only when `DOKIME_CORPUS=1` asks for it, in the job `corpus` of CI
([ADR-0052](../../docs/adr/0052-the-corpus-runs-in-ci-in-a-job-of-its-own-with-the-network.md)).

## The cases

A case is `<project>/cases/<case>/`: a patch on a base commit of the project, a contract, and the
verdict it is expected to get, with its label
([ADR-0055](../../docs/adr/0055-a-case-of-the-corpus-is-labelled-by-how-it-is-built.md)). A good
case holds its `case.toml`, its `contract.yaml` and its `patch.diff`; a bad case holds its
`case.toml` and its `patch.diff`, and uses the contract of the good case it is derived from. The
good patches come from witnesses of the history of the project
([ADR-0057](../../docs/adr/0057-the-cases-of-the-corpus-come-from-witnesses-that-fit-a-boundary.md),
[ADR-0061](../../docs/adr/0061-the-doctests-of-the-documents-are-tests-of-the-pack.md)); the label of
a bad one follows from how it was built.

`review.toml` records that the maintainer confirmed every case before it ran, the date and the
minutes of the review.

## A case does not change

A case is added by one commit and changed by no other, and none of its files is ever deleted or
renamed. The tests read that from the history, so they fail on a shallow clone.

**Correcting a case, even a typo, is withdrawing it and adding a new one.** The new case has a name
of its own; the old one stays as it is, and is listed in `withdrawn.toml` with the reason and the
case that replaces it. A withdrawn case is left out of the counts. This keeps a label or an expected
verdict from changing out of sight after the case has run.

## The tests that need the network

The self-checks, the check that each patch applies on its base, and the check of the witnesses of
the good cases run only when `DOKIME_CORPUS=1` asks for them, which the job `corpus` of CI does. They
clone each project from the directory that `DOKIME_CORPUS_CLONES` names, where the job has cloned
it once, or from its address when there is none.

## The witnesses

The good patch of each case comes from a witness of the history of its project (ADR-0057).
`witnesses.toml` names, for each good case, the commit it comes from and the tests it turned green;
a test looks at each of those commits with the candidates of the self-check on podman and demands
the same. The same file keeps the measurement of ADR-0057: for each project, the commit it started
from and how many candidates and witnesses it found; for each witness, whether it is isolated and
whether it is expressible at a boundary of ADR-0039, each with its reason; and a sample of the
witnesses drawn with a written seed, one expressible and one not in each project, whose examples
were run on both sides of the change to check the reading. The tests demand that the table counts
the witnesses classified, that the witness of each good case is isolated and expressible, and that
the sample is the one its seed draws. The search past the second witness is `witnesses.py`, run by
hand:

```console
$ python -m tests.corpus.witnesses python-semver ../python-semver 25
```
