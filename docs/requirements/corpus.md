# Requirements of the `corpus` scope

The packs of the three repositories of the corpus, the tests that self-check each project at its
commit, and the cases of the corpus with their labels ([ADR-0052](../adr/0052-the-corpus-runs-in-ci-in-a-job-of-its-own-with-the-network.md), [ADR-0055](../adr/0055-a-case-of-the-corpus-is-labelled-by-how-it-is-built.md), [ADR-0057](../adr/0057-the-cases-of-the-corpus-come-from-witnesses-that-fit-a-boundary.md)).
A pack is ours; the code of a project is not copied, it is named by its repository and its commit.
The self-checks need the network, so they run only when asked for, in the job `corpus` of CI. Each
requirement follows an EARS template and has at least one test that declares it in its `SDD-EARS:`
marker.

## The files of a project

- **CORPUS-001** The directory of each project of the corpus shall hold only its `pack.yaml`, its `Dockerfile`, its `source.toml` and the directory `cases` of its cases.
- **CORPUS-002** The `source.toml` of each project shall give the address of its repository and the full name of its commit.
- **CORPUS-003** The pack of each project shall pass the check of packs.
- **CORPUS-004** The Dockerfile of each project shall name its base image by its digest.
- **CORPUS-005** The Dockerfile of each project shall install every package with an exact version and without resolving dependencies of its own.
- **CORPUS-006** The pack of each project shall name as the configuration of its tests `pytest.ini`, `.pytest.ini` and every `conftest.py`, and as its sections those of pytest in `pyproject.toml`, `tox.ini` and `setup.cfg`, whether they exist or not.
- **CORPUS-007** The Dockerfile of each project shall put `/dokime/project/src` on `PYTHONPATH`, since the image does not install the project and the program that observes the examples imports it on its own, without the `pythonpath` of the configuration of pytest.

## The self-check of a project

- **CORPUS-010** When the self-checks of the corpus are asked for, the test of each project shall clone its repository with its whole history and run `dokime env check` at its commit with its pack.
- **CORPUS-011** When the self-check of a project ends, the test shall demand the verdict `PASS`.
- **CORPUS-012** When the self-check of a project ends, the test shall demand that no container and no temporary directory of the run is left.
- **CORPUS-013** If cloning the repository of a project fails, then the test shall fail with a message that starts with `network:` and names the address.
- **CORPUS-014** If the self-checks of the corpus are not asked for, then the test of each project shall skip.
- **CORPUS-015** Where `DOKIME_CORPUS_CLONES` names a directory, the test of each project shall clone its repository from the clone of that directory named after the project, instead of from its address.

## The cases ([ADR-0055](../adr/0055-a-case-of-the-corpus-is-labelled-by-how-it-is-built.md), [ADR-0057](../adr/0057-the-cases-of-the-corpus-come-from-witnesses-that-fit-a-boundary.md))

A case is a directory `tests/corpus/<project>/cases/<case>/`. A good case holds its `case.toml`, its
`contract.yaml` and its `patch.diff`; a bad case holds its `case.toml` and its `patch.diff`, and
uses the contract of a good case of its project.

| Field of `case.toml` | Holds | In |
|---|---|---|
| `project` | The name of the directory of its project | Every case |
| `base` | The full name of the commit the patch applies to | Every case |
| `contract` | `contract.yaml` in a good case; the path of the contract of a good case of the project, from the directory of the case, in a bad case | Every case |
| `patch` | `patch.diff` | Every case |
| `label` | `good`, `fails-a-visible-example`, `edits-tests` or `breaks-existing-tests` | Every case |
| `how` | How the patch was built, in one line | Every case |
| `expected` | `PASS` for a good case, `FAIL` for a bad one | Every case |
| `intent` | What the patch tries, in one line | A bad case |
| `mechanism` | How it tries it, in one line | A bad case |
| `failing_gate` | The gate expected to give `FAIL` first: `visible-examples`, `protected-paths` or `existing-tests` | A bad case |

### The files of a case

- **CORPUS-020** The corpus shall hold ten cases: three good, and seven bad that are derived from them.
- **CORPUS-021** The directory of a good case shall hold only its `case.toml`, its `contract.yaml` and its `patch.diff`.
- **CORPUS-022** The directory of a bad case shall hold only its `case.toml` and its `patch.diff`.
- **CORPUS-023** The `case.toml` of each case shall hold the fields of the table of the cases that it is in, and no other.
- **CORPUS-024** The `project` of each case shall be the name of the directory of its project.
- **CORPUS-025** The `base` of each case shall be the full name of a commit.
- **CORPUS-026** The `expected` of each case shall be `PASS` when its `label` is `good`, and `FAIL` otherwise.
- **CORPUS-027** The `contract` of each bad case shall name the contract of a good case of the same project and the same base.
- **CORPUS-028** The contract of each good case shall pass the check of contracts with no finding.
- **CORPUS-029** The `story` of the contract of each good case shall be the name of the directory of the case.

### The labels do not change ([ADR-0055](../adr/0055-a-case-of-the-corpus-is-labelled-by-how-it-is-built.md))

A label never changes after the case ran: a correction is a new case, and the old one is withdrawn
in `tests/corpus/withdrawn.toml` without touching its files.

- **CORPUS-030** The files of each case shall be added by one commit, and changed by no other.
- **CORPUS-031** If a file of a case was deleted or renamed in the history, then the test of the cases shall fail naming it.
- **CORPUS-032** If the history of the repository is shallow, then the test of the cases shall fail instead of passing.
- **CORPUS-033** The file `tests/corpus/review.toml` shall name every case as confirmed by the maintainer, with the date and the minutes of the review.

### The patches apply

- **CORPUS-040** When the tests of the corpus are asked for, the test of each case shall check with `git apply --check` that its patch applies on its base, in a clone of its project.
- **CORPUS-041** If the patch of a case does not apply on its base, then the test shall fail naming the case and quoting what git said.

### The witnesses of the good cases ([ADR-0057](../adr/0057-the-cases-of-the-corpus-come-from-witnesses-that-fit-a-boundary.md))

The good patch of each case comes from a witness of the history of its project. The search past the
second witness is `tests/corpus/witnesses.py`, run by hand; its measurement of ADR-0057 and the
witnesses of the good cases are the fixture `tests/corpus/witnesses.toml`. The same fixture keeps
the two filters of ADR-0057 for each witness of the measurement, read from its diff, and a sample of
them drawn at random and run, which says how often the reading is right.

- **CORPUS-045** When the tests of the corpus are asked for, the test of each witness of the fixture shall look at its commit with the candidates of the self-check on the git and the podman adapters, and demand that it is a witness that turns green the tests the fixture names.
- **CORPUS-046** The fixture shall name, for each good case, the witness it comes from, whose parent is the base of the case.
- **CORPUS-047** The table of the measurement in the fixture shall give, for each project of the corpus, as many witnesses as the fixture classifies for it.
- **CORPUS-048** The witnesses of each project in the table of the measurement shall be no more than its candidates looked at.
- **CORPUS-056** The fixture shall give, for each witness it classifies, whether it is isolated and whether it is expressible, each with its reason, and a boundary, `function` or `cli`, with its target exactly when it is expressible.
- **CORPUS-057** The fixture shall classify each witness once, and classify the witness of each good case as isolated and expressible.
- **CORPUS-058** The sample of the fixture shall be the one that its written seed draws: in each project, in the order of the fixture, one witness among those that are expressible and one among those that are not.
- **CORPUS-059** The fixture shall give, for each witness of the sample, the example tried at its boundary, what it gave before and after the change, and whether that confirms the reading, and for one that is not expressible, why the example cannot be written.
- **CORPUS-060** The fixture shall keep a second reading of every witness it classifies, made without seeing the first, with whether it is isolated and whether it is expressible and its reason.
- **CORPUS-061** The fixture shall give, for each filter and for both together, how many witnesses the two readings label alike, as the two readings give it.

### The audit of the cases

The exit criterion of A3 is measured on the ten cases: no false accept on patches that fail visible
examples, edit tests or break existing tests.

- **CORPUS-050** When the tests of the corpus are asked for, the test of each case shall audit its patch on its base with the command `audit`, in a clone of its project, with the pack of the project and the contract of the case given from outside the patch.
- **CORPUS-051** When the audit of a case ends, the test shall demand the verdict that the `expected` of the case names.
- **CORPUS-052** When the audit of a bad case ends, the test shall demand that the first gate, in the order of the audit flow, whose verdict is `FAIL` is the `failing_gate` of the case.
- **CORPUS-053** When the audit of a case ends with evidence, the test shall demand that the evidence reads back without a finding.
- **CORPUS-054** When the audit of a case ends, the test shall write one line with the case, its verdict and its `expected`, and the first gate that failed and its `failing_gate`, so that the job shows the measurement of every case.
- **CORPUS-055** When the gate `repeatability` ran in the audit of a case, the test shall demand that its evidence carries `repeated` with `runs` as `2`, as many as the policy of the case says by default, and `consistent` as `true`; and that it carries no `repeated` when the gate did not run.

### The hold-out by hand (B0, [ADR-0014](../adr/0014-hidden-checks-are-held-out-approved-examples.md))

`tests/corpus/holdout-by-hand/` keeps copies of the three good contracts of the corpus with more
examples in the cases of their requirements of change, approved by the maintainer; the split of
their examples into visible and held-out, drawn with a written seed; and the patches that agents
wrote seeing only the visible examples, with the audits they gave. The contracts of the ten cases
are not touched.

- **CORPUS-062** The fixture of the hold-out by hand shall have at least two examples in each case of a requirement of change of each of its contracts.
- **CORPUS-063** The held-out examples of the fixture shall be the ones that its written seed draws: one in each case of a requirement of change, chosen in the order of the contracts and of their examples.
- **CORPUS-064** When the tests of the corpus are asked for, the test of each patch that special-cases the visible examples shall demand that the audit with only the visible examples gives `PASS`, and that the audit with all the examples fails at `visible-examples` on exactly the held-out examples.
- **CORPUS-065** The fixture shall record, for each patch that an agent wrote, its kind and the verdicts of its audits with the visible examples and with all the examples.

### The sealed run of B1 ([ADR-0014](../adr/0014-hidden-checks-are-held-out-approved-examples.md), [ADR-0075](../adr/0075-the-predicate-v0-3-records-the-hold-out.md))

The three contracts of B0 sealed with `contract seal`, each in a local clone of its project on the
base of its case, and the patches of B0 audited on them with the key. Their examples are public in
this repository, outside the history of the projects, so the run measures the mechanism and not
the value of a hold-out with secret examples, which B3 and B4 measure.

- **CORPUS-066** The fixture of the sealed run shall record, for each contract of B0, the base of its batch, its seed, its held-out examples, the examples kept visible and each case without a held-out example with its motive, as the batch holds them.
- **CORPUS-067** The fixture of the sealed run shall record, for each patch of B0 and each patch written for the seal, the verdict, the gate and the outcome of the gate `sealed-examples` that it expects, with the reason.
- **CORPUS-068** The fixture of the sealed run shall keep, for each contract, the visible contract and the sealed batch of the seal, whose examples are those of the contract of B0 without the held-out ones and whose entries `held_out` name the held-out examples that it records.
