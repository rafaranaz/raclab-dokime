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
| `label` | `good`, `fails-a-visible-example`, `edits-tests`, `breaks-existing-tests` or, from B2, `breaks-a-relation` | Every case |
| `how` | How the patch was built, in one line | Every case |
| `expected` | `PASS` for a good case, `FAIL` for a bad one | Every case |
| `intent` | What the patch tries, in one line | A bad case |
| `mechanism` | How it tries it, in one line | A bad case |
| `failing_gate` | The gate expected to give `FAIL` first: `visible-examples`, `protected-paths`, `existing-tests` or `relations` | A bad case |

### The files of a case

- **CORPUS-020** The corpus shall hold, leaving out its withdrawn cases, thirty-two cases: ten good, and twenty-two bad that are derived from them.
- **CORPUS-021** The directory of a good case shall hold only its `case.toml`, its `contract.yaml` and its `patch.diff`, and its `sealed.age` when its contract holds out examples.
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
in `tests/corpus/withdrawn.toml` without touching its files. A case runs for the first time once it
is in `main` with its label: until then `tests/corpus/pending.toml` lists it, a file apart, so that
taking it out of the list changes none of its files. The labels follow what the exit criterion of
a milestone names: those of A3, and `breaks-a-relation` for B2.

- **CORPUS-030** The files of each case shall be added by one commit, and changed by no other.
- **CORPUS-031** If a file of a case was deleted or renamed in the history, then the test of the cases shall fail naming it.
- **CORPUS-032** If the history of the repository is shallow, then the test of the cases shall fail instead of passing.
- **CORPUS-033** The file `tests/corpus/review.toml` shall hold each review of the maintainer, with its date, its minutes and the cases it confirmed, and name every case that is not pending as confirmed by one of them.
- **CORPUS-073** The file `tests/corpus/pending.toml` shall list the cases that have not run yet, each a case of the corpus, and may list none.
- **CORPUS-074** When the tests of the corpus are asked for, the test of the audit of the cases shall leave out each case that `tests/corpus/pending.toml` lists.

### The intent of each contract

Each good case has an intent sentence: what someone would say before writing any example, for a
later experiment where a model writes the contract from it. It is taken from the project of the
case, quoted as it is, from the title of its issue, else of its pull request, else the message of
its commit; when none is usable, the maintainer writes it before seeing the examples, and an entry
for a case whose contract the maintainer had already seen says so. A sentence is one or two
sentences, and holds no concrete value of the inputs or of the outputs of the examples, nor the name
of a test, though it may name the behaviour or the error it asks for; a quotation that holds such a
value is not usable, and the entry may say why a source was skipped. A bad case has none, since it
uses the contract of its good case.

- **CORPUS-075** The file `tests/corpus/intents.toml` shall give each good case, by its key, an intent sentence and its source: `issue:` or `pr:` and the address, `commit:` and the full name of the commit, or `maintainer`.

### The blind reading of the witnesses

The test of ADR-0074 in B3a: two new readers label the 41 witnesses again with its four conditions
only, each batch in a conversation of its own, in an order drawn with a seed. Its criterion, how an
undecidable counts and its limits were recorded in `tests/corpus/blind/criterion.toml` before the
reading; its result is kept in `tests/corpus/blind/result.toml`, which the tests recompute from the
answers.

- **CORPUS-076** The file `tests/corpus/blind/draw.toml` shall give each witness of the measurement the id that its seed draws, and each batch the digest of its file.
- **CORPUS-077** The answers of `tests/corpus/blind/answers` shall give each reader one label for each witness, the last when an answer labels a witness twice.
- **CORPUS-078** The file `tests/corpus/blind/result.toml` shall give the kappa and the raw agreement of the two readers on isolated, over the 41 witnesses and over the eight in dispute, with an undecidable counted as not isolated and a kappa without variation given as undefined.
- **CORPUS-079** The file `tests/corpus/blind/result.toml` shall give the undecidable labels of each reader by condition, and the kappa and the raw agreement over the witnesses that neither reader called undecidable.

### The reading of the boundary

B3c reads the 21 witnesses that are not expressible today against four options for the boundary
`function`, fixed in `tests/corpus/boundary/options.toml` before any reading: by the session that
builds the work, and by the session that reviews it, which does not see the first reading. The
maintainer resolves the differences in `tests/corpus/boundary/resolution.toml`, and
`tests/corpus/boundary/result.toml` keeps what the tests recompute.

- **CORPUS-080** The file `tests/corpus/boundary/batches.toml` shall give each batch of the second reading the witnesses it holds and the digest of its file.
- **CORPUS-081** The readings of `tests/corpus/boundary` shall label each witness that is not expressible today once for each option of `options.toml`.
- **CORPUS-082** The file `tests/corpus/boundary/resolution.toml` shall resolve each witness and option that the two readings label apart, and no other, by a precision of `options.toml`.
- **CORPUS-083** The file `tests/corpus/boundary/result.toml` shall give, for each option, the witnesses that fit it, among them those that both new readers of B3a label isolated, and how many of the isolated witnesses of the 41 are expressible with it.

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
- **CORPUS-057** The fixture shall classify each witness once, and classify the witness of each good case as isolated, and as expressible unless the reading of the boundary in `tests/corpus/boundary/result.toml` gives that the witness fits the option `a` of [ADR-0079](../adr/0079-an-example-at-function-may-call-the-methods-of-an-object.md).
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

### Cases with a sealed batch

A case whose contract holds out examples keeps only the visible contract and its `sealed.age`; the
held-out examples are never written in clear in the repository. The gate `sealed-examples` reads
both from the base, so the test audits such a case on a commit of its own on top of the base. In CI
the key is not there, and a case that only the hold-out catches is judged on that; with the key, in
a run that the maintainer starts, it is judged on its `expected`.

- **CORPUS-084** When a case whose contract has a `sealed.age` is audited, the test shall audit it, with the story of the contract, on a commit that adds the contract and the `sealed.age` in `.dokime/changes/<story>/` on top of the commit of the recipients that the contract was sealed on, made again on the base of the case.
- **CORPUS-085** While the key is not given to the test, when the audit of a case labelled `fails-a-held-out-example` ends, the test shall demand that no gate gave `FAIL` and that the gate `sealed-examples` is not applicable because the key is not here.
- **CORPUS-086** Where `DOKIME_CORPUS_IDENTITY` names an identity, the test shall audit each case with a `sealed.age` with that identity, asking its passphrase once and giving it to each audit by a descriptor.
- **CORPUS-087** The file `tests/corpus/held-out-run.toml` shall give, for each run with the key, its date and, for each case it audited, the verdict and the first failing gate.
- **CORPUS-088** The verdict and the first failing gate that `tests/corpus/held-out-run.toml` gives for a case shall be its `expected` and its `failing_gate`.

The command that seals reads the recipients from `.dokime/recipients.txt` in the tree of the
project and gives the batch, as its base, the commit of the checkout; the gate `sealed-examples`
refuses a batch whose base is not in the history of the change. A contract of the corpus is sealed
on a commit of the recipients on top of the base of its case, which is not in the project, so the
test makes it again, from what was recorded, before it commits the contract and the batch on top.

- **CORPUS-092** The file `tests/corpus/seal-bases.toml` shall give, for each contract with a `sealed.age` of a case that is not withdrawn, the base, the text of `.dokime/recipients.txt`, the author, the date and the message of the commit of the recipients that it was sealed on, the hash of that commit, and the event of the ledger of the seal that the hash comes from.
- **CORPUS-093** If the commit of the recipients made again does not have the hash that `tests/corpus/seal-bases.toml` gives, then the test shall stop before the audit with an error that names the contract and both hashes.
- **CORPUS-094** The tests of the corpus shall make again, without the key, the commit of the recipients of each contract that `tests/corpus/seal-bases.toml` lists, and find the hash that it gives.
- **CORPUS-095** When the tests of the corpus audit, with an identity made for the test and on the commit that the test of the cases makes, a contract sealed with that identity on a commit of the recipients on top of a base, the tests shall demand that the gate `sealed-examples` runs without a finding.

The audit of a case is given an empty `XDG_DATA_HOME`, so that `audit` finds no identity where it
looks for one by default; podman keeps its storage there too. One such directory serves every case
of a session of pytest, so that the images of a part are kept once and not once for each case.

- **CORPUS-096** The tests of the corpus that audit a case shall give every audit of a session of pytest the same `XDG_DATA_HOME`, a directory made empty for that session.
- **CORPUS-097** If the `XDG_DATA_HOME` of a session holds `dokime/identity.age` when the session starts or when it ends, then the tests of the corpus shall fail, naming the file.

### The results of a run ([ADR-0081](../adr/0081-bench-computes-the-metrics-from-the-results-that-the-corpus-writes.md))

The test of the cases runs the audits and `bench` computes the metrics from what it writes: one line
of JSON for each case, with the commit of this repository that the run was made on, so that two
files can be told to come from the same commit.

- **CORPUS-098** Where `DOKIME_CORPUS_RESULTS` names a file, the test of the cases shall append to it, for each case it audits and before it judges the case, one line of JSON with the commit of this repository, the key of the case, its verdict, its first failing gate or `null`, and whether the key was given.
- **CORPUS-099** The metrics that `tests/corpus/runs/<commit>/bench.json` keeps for a run shall be those that `bench` gives of the files of results of that run kept next to it, with `tests/corpus` as it was at the commit of the run.

### Withdrawn cases ([ADR-0055](../adr/0055-a-case-of-the-corpus-is-labelled-by-how-it-is-built.md))

A case that turns out wrong after it ran is not corrected: it is withdrawn, its files stay as they
were, and a new case replaces it. What its first run gave is kept, since a good case that failed
because of its contract is a false reject that `bench` reports apart.

- **CORPUS-089** The file `tests/corpus/withdrawn.toml` shall give each withdrawn case its key, the reason, and the verdict and the first failing gate of its first run, with whether the key was given.
- **CORPUS-090** Where the case that replaces a withdrawn case is in the corpus, the file `tests/corpus/withdrawn.toml` shall name it for the withdrawn case.
- **CORPUS-091** The tests of the corpus shall leave every withdrawn case out of the audit of the cases and out of the count of the cases.

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
- **CORPUS-069** When the tests of the corpus are asked for, the test of the sealed run shall commit the visible contract and the sealed batch of the fixture on the base of a case in a clone of its project, audit a patch without the key, and demand that the gate `sealed-examples` is not applicable with the reason `the key is not here`.
- **CORPUS-070** When the tests of the corpus are asked for, the test of the audit of each case shall demand that the gate `sealed-examples`, when the run reaches it, is not applicable with the reason `the contract holds out no example`.
- **CORPUS-071** When the tests of the corpus are asked for, the test of the sealed run shall seal a contract with an identity made for the test, audit a patch with that identity and its passphrase through a descriptor, and demand that no call of git or podman holds the path of the identity or its passphrase in its arguments, its environment or its build context, nor inherits the descriptor.
- **CORPUS-072** The fixture of the sealed run shall record, for each patch, the verdict, the gate and the outcome of the gate `sealed-examples` that its sealed audit gave, each equal to the one it expected, and keep the evidence of that audit, which holds the hold-out when the gate observed and names no held-out example.

### The contrast with swarm-verify (R2)

R2 runs swarm-verify 3.1.0 on the cases of the corpus in three arms; `tests/corpus/contrast/` holds
the conversion of the examples of a contract into black-box checks that swarm-verify can run, for
the arm S2, and the adaptations of each project. Nothing of it runs on the corpus before the
criteria of R1 are approved.

The held-out examples of the corpus exist in clear only on the machine of the maintainer: the
conversion of the held-out examples, their sealing for swarm-verify and the runs of S1 and S2 with
sealed checks happen there, by commands that come with the runs of R2 and are reviewed before they
run, because swarm-verify keeps its sealed checks, and the evidence of each run, in clear. What
leaves that machine is the status of each case and the counts of each arm, after review.

- **CORPUS-100** When examples of a contract are converted, the conversion shall write a new directory with the program that observes of dokime and the modules `core`, `contract`, `oracle` and `sandbox` of dokime, each as it is in `src/dokime`, one file for each example, a runner and a test file of pytest.
- **CORPUS-101** When an example is converted, the conversion shall write it as JSON from which the runner rebuilds the same example that dokime read from the contract, its expectations included, with no code run to read it.
- **CORPUS-102** If the directory to write already exists, or an id names no example of the contract, or the contract has a finding that keeps it from being read, then the conversion shall refuse with a message that says why and write nothing.
- **CORPUS-103** When the runner is run on an example from the root of a project, the runner shall observe the example with the program that observes in a process of its own, give it the request that the podman adapter gives for that example, and compare the observation with the oracle of dokime.
- **CORPUS-104** When the example holds, the runner shall exit with 0, and when it does not hold, with 1.
- **CORPUS-105** If the program that observes ends with an error, then the runner shall exit with 2.
- **CORPUS-106** Where the project has `.venv/bin/python`, the runner shall run the program that observes with it, so that the child imports what the environment of the project installed.
- **CORPUS-107** When pytest collects the test file, the test file shall give one test for each example converted, which passes only when the runner exits with 0 for that example.
- **CORPUS-108** The file of the adaptations shall give, for each project, the files that it adds to a local copy of the base, the image, the command of setup and the command of the tests, and the minutes that the adaptation cost, and nothing else; the minutes are a whole number for every project of the corpus, and only a project outside it may give `"not measured"`.
- **CORPUS-109** Where a module of the contrast in `tests/corpus/contrast/` is not the command of the runs `maintainer.py`, the module shall open no sealed batch of the corpus and use no identity of the sealed store, so that the held-out examples of the corpus are in clear only where the maintainer runs that command.
- **CORPUS-110** The file of the adaptations shall give an entry for every project of the corpus that has a case, so that every case of R2 runs with the adaptation of its project.
- **CORPUS-111** The file of the adaptations shall give the image of every entry pinned by its digest, so that every run of a project uses the same image.

#### The runs of R2

`maintainer.py` runs the three arms on the machine of the maintainer, with docker, and is reviewed
before it runs. It opens the sealed batches of the corpus there with the identity of the maintainer,
so it is never run with that identity on the machine where this code is written, and its tests use
an identity and a batch made for them. `run_arm.mjs` gives one request to swarm-verify, pinned by
`package-lock.json`.

- **CORPUS-112** The package of the contrast shall pin swarm-verify to the version 3.1.0 with its integrity `sha512-xpAfXmNioZQVadKqldljIjLX6cAtLAqxqU08CFZ1Nu6Qt6Ha7saJBd0UZsTUksue5oTb/u2XnHcrhU95e8DlGw==`.
- **CORPUS-113** When the helper of Node is given a request on its input, the helper shall seal the files that the request gives in memory with `sealFiles`, when it gives any, call `verify()` of swarm-verify, and write the result as JSON on its output.
- **CORPUS-114** If the variable `DOKIME_CORPUS_IDENTITY` does not name a file, then the command of the runs shall refuse with a message that says so and run nothing.
- **CORPUS-115** When the command of the runs is run, the command shall run the arms S0, S1 and S2 for each case of the corpus that is not withdrawn, each in a local copy of the base of the case with the adaptation of its project and the patch of the case on top, and keep the evidence of each run in the directory given.
- **CORPUS-116** When the command runs an arm, the command shall give swarm-verify a `SWARM_HOME` in a directory of its own and delete that directory when the run ends.
- **CORPUS-117** When the command runs the arm S1, the command shall seal the files of the tests of the pack that the witness of the good case changed, as they are at the witness, with a check that runs the command of the tests of the adaptation.
- **CORPUS-118** When the command runs the arm S2, the command shall lay the conversion of the visible examples of the contract in the base, give it as a check of authority `user-acceptance`, and seal the conversion of the held-out examples of its batch, when the contract holds out any, under names that carry no id of an example.
- **CORPUS-119** The command shall give the held-out examples to the helper of Node only through its input, and write none of them to a file.
- **CORPUS-120** When a run ends, the command shall write in the file of the results one entry with the key of the case, the arm, the state and the regression that swarm-verify gave, the tests of the visible checks and of the held-out checks that passed and that did not pass, whether the rejection comes only from the strict-xfail test of mdformat, and the kind of failure of the mount, and nothing else.
- **CORPUS-121** When the command counts the held-out tests of a run, the command shall count, in S1, the tests that the witness turned green and, in S2, the tests of the sealed conversion, each as it ran in the sealed check.
- **CORPUS-122** When swarm-verify does not give the state `complete` and the only test of the run that failed is the test of mdformat that the witness `27e2ba3` takes out of `xfail`, the command shall record that the rejection comes only from that test.
- **CORPUS-123** If the mount of a run fails, or the helper of Node ends with an error, then the command shall record the kind of failure, `mount` or `helper`, with no message, and go on with the next run.
