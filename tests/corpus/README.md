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
case that replaces it once it is added, and what its first run gave: the verdict, the first
failing gate and whether the key was given. A withdrawn case is left out of the audit and of the
counts; `bench` reports it apart, a good case among them as a false reject caused by its contract. This keeps a label or an expected
verdict from changing out of sight after the case has run.

## Cases with a sealed batch

A good case whose contract holds out examples keeps only the visible contract and its `sealed.age`,
sealed for an identity whose key stays on the machine of the maintainer, never in the repository nor
in CI; the held-out examples are never written in clear. The test audits such a case on a commit on
top of its base that adds both at `.dokime/changes/<story>/`, since the gate `sealed-examples` reads
them from the base (`sealing.py`). A bad case that only the hold-out catches is labelled
`fails-a-held-out-example`, with `sealed-examples` as its failing gate: in CI, where the key is not,
the test demands that no gate fails and that `sealed-examples` is not applicable as the key is not
here; with `DOKIME_CORPUS_IDENTITY`, in a run that the maintainer starts and gives the passphrase
to once, it demands its `expected`, and `held-out-run.toml` records each such run.

The command that seals reads the recipients from `.dokime/recipients.txt` in the tree it seals in,
and gives the batch, as its base, the commit of that checkout; the gate refuses a batch whose base
is not in the history of the change (`sealed-batch-mismatch`). A contract is therefore sealed on a
commit of the recipients on top of the base of its case, which is in no repository: `seal-bases.toml`
keeps, for each contract, what makes that commit again (the base, the text of the file, the author,
the date and the message) and its hash, taken from the event `run.started` of the ledger of the
seal. The test makes it again, stops before the audit if its hash is another, and commits the
contract and the batch on top of it. A test without the key makes the commits again, and another
seals a contract with an identity made for it and audits it with that identity through the same
path.

A seal made from now on follows one convention, so that its commit of the recipients can be made
again from the base alone: the file holds the recipient of the corpus and a newline, the author and
the committer are `dokime corpus <corpus@dokime.invalid>`, both dates are the committer date of the
base, as `git log --format=%cd --date=raw` gives it, and the message is `the recipients of the
corpus`. Its entry in `seal-bases.toml` is still written, with the hash from the ledger.

Each audit is given an empty `XDG_DATA_HOME`, so that `audit` finds no identity where it looks for
one by default, and podman keeps its storage under it. One such directory serves the whole session
of pytest (`conftest.py`, `data_home.py`): the cases of a part share the images, the session fails
if `dokime/identity.age` is in it at its start or its end, and its end prints the space the storage
takes. A limit: an image that comes from that storage does not show that it would build from
nothing today; in CI each part starts from an empty one, so its first case builds cold.

With `DOKIME_CORPUS_RESULTS` naming a file, the test of the cases appends to it one line of JSON
for each case it audits, before it judges the case (`results.py`, ADR-0081): the commit of this
repository, the key of the case, its verdict, its first failing gate or `null`, and whether the key
was given. `bench` computes the metrics from such files. The commit is that of `HEAD`: a run made
with changes that are not committed gives it all the same, so a file of results is only worth its
commit when the tree was clean; in CI it always is. On a `pull_request` the job `corpus` checks out the
merge commit that GitHub makes, so the file of results of a pull request records a commit that no
longer exists once the pull request is merged by rebase. The figures of a version are therefore
taken from runs on a push to `main`, where the commit is real; for stability, running the same job
again is enough, since it reuses the same commit. `runs/<commit>/` keeps the files of results that a
figure of the roadmap rests on, since an artifact of CI expires, with `run.toml`, which says where
each comes from, and `bench.json`, what `bench` gave of them; a test computes it again.

## The intent of each contract

`intents.toml` gives each good case, by its key, an intent sentence: what someone would say before
writing any example, for a later experiment where a model writes the contract from it. It is quoted
from the project of the case, from the title of its issue, else of its pull request, else its commit
message, with its source; when none is usable, the maintainer writes it before seeing the examples
(`maintainer`, and `seen_contract = true` for a case whose contract had already been seen). A
sentence holds no concrete value of the inputs or of the outputs of the examples, nor the name of a
test, though it may name the behaviour or the error it asks for: "Preserve constructor TypeError in
Version.replace" is usable, while a title that names the character of the input of an example is
not, and `skipped` says so. It lives apart from the files of a case, which do not change.

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
were run on both sides of the change to check the reading. It keeps too a second reading of every
witness, made without seeing the first, and how many witnesses the two label alike, which a test
computes again. The tests demand that the table counts
the witnesses classified, that the witness of each good case is isolated and expressible, and that
the sample is the one its seed draws. The search past the second witness is `witnesses.py`, run by
hand:

```console
$ python -m tests.corpus.witnesses python-semver ../python-semver 25
```

## The blind reading of the witnesses

`blind/` is the test of ADR-0074 in B3a: two new readers label the 41 witnesses again with its four
conditions only, each batch in a conversation of its own, without a project, memory or the search of
the web. `draw.toml` keeps the seed of the order, the witness of each id and the digest of each
batch; `batch-*.txt` are the batches as they were given, each with its prompt; `criterion.toml` the
criterion, how an undecidable counts and the limits, recorded before the reading; `answers/` each
answer as it was copied, `discarded.toml` the attempts that did not get the whole batch, and
`result.toml` the result. The tests demand that the order is the one its seed draws, that each batch
is the file that was given, that each answer labels the witnesses of its batch, and that the result
is the one the answers give.

## The reading of the boundary

`boundary/` is the reading of B3c: the 21 witnesses that are not expressible today, read against
four options for the boundary `function`. `options.toml` keeps what fits means, the four options and
the criteria to compare them, recorded before any reading, and two precisions decided after both
readings; `first-reading.txt` is the reading of the session that builds the work,
`second-reading.txt` that of the session that reviews it, made from `batch-*.txt` without seeing
the first; `resolution.toml` the labels of the maintainer where they differ, and `result.toml` what
each option lets fit. The tests demand that each batch is the file that was given, that each reading
labels each witness once for each option, that the resolution covers the pairs read apart and no
other, and that the result is the one the readings give.

## The hold-out by hand

`holdout-by-hand/` is B0, the hold-out of ADR-0014 tested by hand before B1 builds it. It keeps
copies of the three good contracts with more examples in the cases of their requirements of
change, approved by the maintainer, and `holdout.toml`: the seed of the split, the example held out
in each case of change, the minutes of the review, and the six patches of agents in `patches/`,
written by new agents that saw only the visible examples, with the verdicts of their audits. Three
were asked for the minimum and three to special-case the visible inputs. A test draws the split
again from the seed, and, when the tests of the corpus are asked for, audits each special-cased
patch with the visible examples, where it passes, and with all of them, where it fails on exactly
the held-out examples. The contracts of the ten cases are not touched.
