# Roadmap

*Leer en [español](ROADMAP.es.md).*

Each phase has exit criteria. **The next phase does not open until the previous one meets all of
them** ([ADR-0003](adr/0003-rules-enforced-in-ci.md)). If a criterion turns out to be impossible or
wrong, it is changed here in its own pull request with its reason, not skipped.

## Phase 0 · Working agreement and gates — done

Working rules, CI pipeline and development skills, with no harness code.

Exit criteria:

- [x] Reproducible environment: pinned Python, dependencies in `uv.lock`, installed with
  `--locked`.
- [x] Quality, governance, discipline and audit gates in CI, each with EARS requirements and tests
  ([docs/requirements/repo.md](requirements/repo.md)).
- [x] Working agreement documented in [CONTRIBUTING.md](../CONTRIBUTING.md).
- [x] ADRs for the process decisions.
- [x] Development skills in `.claude/skills/`.
- [x] Documentation in English and Spanish, with translations checked in CI.
- [x] CI green on the phase pull request in GitHub.
- [x] Protection of `main` enforced in GitHub (see below).

## Phase 1 · Reference architecture — done

The architecture of the product, decided with evidence. Every decision is an ADR that states what
it rests on (literature, reasoning or a test) and the alternatives considered
([ADR-0008](adr/0008-built-new-nothing-is-ported.md)). It is delivered in milestones, each one a
pull request reviewable on its own:

| Milestone | What it delivers | Scope |
|---|---|---|
| 1.1 Map and decisions | What the product is and states, the invariants, the context, the trust zones, the modules with their allowed dependencies, and the ADRs 0008 to 0032 | `arch` |
| 1.2 Governance aligned | A check that every ADR from 0008 on states its basis; the working agreement aligned with the blocks of phase 2 | `repo` |
| 1.3 Data and evidence | The contract and example formats, the evidence predicate, the ledger and the end-to-end sequence of a change | `arch` |
| 1.4 States and flows | The schema of the flow file, the states, the gates, the budgets, the composition per mode and the rules of the validator | `arch` |
| 1.5 Import contracts | The dependency rules of the module map, checked in CI (import-linter) | `repo` |
| 1.6 Phase closed | Exit criteria marked and the hypotheses listed with their test and their block | `arch` |

Data and evidence comes before states and flows because block A depends on the formats, while the
flow file is not used until block C. Each module gets its high-level EARS requirements when its
scope is opened in phase 2.

Before they were accepted, the decisions were checked against the ten invariants by three
independent attempts. The corrections, a glossary and the ADRs 0033 to 0035 came from that check
and from writing the formats down.

Exit criteria:

- [x] The documents above are in `docs/architecture/` and their diagrams pass validation.
- [x] Every ADR from 0008 on is accepted or explicitly left as a hypothesis with its test.
- [x] The check that every ADR states its basis and the import contracts are in CI.
- [x] The architecture is approved in review.

## Phase 2 · Construction in blocks

Seven blocks, each delivering something a person can use and a published version
([ADR-0029](adr/0029-build-order-starts-with-auditing.md)). Inside a block, one module scope is
open at a time, in the order listed. A block closes when its exit criterion, measured on the
corpus ([ADR-0030](adr/0030-the-harness-is-measured-on-a-corpus-with-known-verdicts.md)), is met
and published. A bad result is published as well.

| Block | What a user can do when it closes | Modules, in order | Exit criterion | Version |
|---|---|---|---|---|
| A · Audit | Verify a finished change, made by any agent, against a hand-written contract, locally and in CI | `core`, `contract`, `packs`, `sandbox` (verification runtime), `platform` (project repository, stores and clock), `verify`, `evidence`, `interfaces` | No false accept on patches that fail visible examples, edit tests or break existing tests | 0.1 |
| B · Hold out | The same, with examples the agent never saw | `oracle`, `platform` (sealed store), `verify`, `bench` | No false accept on the four cheating techniques; value of the hold-out measured | 0.2 |
| C · Launch | Hand the task to the harness and let it drive the agent until the change passes or it asks | `sandbox` (work), `agents`, `engine` | The same change completes the circuit with two agent profiles, one with an open-weight model | 0.3 |
| D · Protect | Know what the change damages outside what was asked | `verify` | Injected regressions in covered code are detected; rate of questions measured | 0.4 |
| E · Attest | Deliver signed evidence that a third party verifies without the harness | `platform` (signing and forge), `evidence`, `delivery` | Someone without the harness installed verifies an evidence file | 0.5 |
| F · Specify | Write the contract with help, in Spanish or English | `gateway`, `spec` | Minutes of a person per contract measured; the attention test done | 0.6 |
| G · Generalise | Use it with a second language, more agents and in a team | `packs`, `agents`, `delivery` | The corpus includes a Java repository; three different agents complete the circuit | 1.0 |

The milestones of a block are written here when the block opens, and its measured numbers when it
closes. The order of blocks B and C is confirmed when block A closes.

**Block A is open.** Its first milestone, A0, has no code: it tests by hand the formats that the
rest of the block depends on.

**A0 is done.** Three hand-written contracts were made on changes that public projects already
made (a pull-request description cleaner, `humanize.naturalsize`, `tabulate` pipe escaping), each
checked by running its examples against the code before and after the change. All nine
requirements fit as examples at a boundary. The person approved them. Reading took about 4 to 5
minutes for the pull-request cleaner, about 2 for `naturalsize` and about 3 for `tabulate`, whose
formats the person did not know; these are the person's own estimates, not measurements. What it changed in
the format is in [the contract](architecture/03-data-and-evidence.md#the-contract). The
three repositories of the corpus are other ones, so that what is known of the A0 projects does not
leak into the tests: [cachetools](https://github.com/tkem/cachetools) (MIT),
[python-semver](https://github.com/python-semver/python-semver) (BSD-3-Clause) and
[mdformat](https://github.com/executablebooks/mdformat) (MIT). All three are pure Python, install on
Python 3.13 and their suites pass in under 15 seconds (416, 512 and 4286 tests); two of them have a
command-line boundary (`pysemver`, `mdformat`) and all have a function boundary. They have 72, 25 and
38 commits with "fix" in the message that touch tests, which is a count of candidates, not of usable
cases.

**A1 is done.** `dokime contract check` validates a contract file and says what it lacks, with one
line for each finding and an exit code for each verdict
([ADR-0040](adr/0040-commands-exit-with-a-code-for-each-verdict.md)). It was built in three modules:
`core` (verdicts, findings and the strict reader of
[ADR-0037](adr/0037-a-contract-is-read-by-strict-rules-of-its-own.md)), `contract` (the check) and
`interfaces` (the command). The three contracts of A0, rewritten to the rules that A1 fixed, pass
without a finding. Its exit criterion is met: with a text that is not EARS, a requirement without
an example, a duplicate and a contradiction seeded in one of them, the command reports the four in
one run. The defects of reading (a repeated key, a value whose type depends on the reader, a text
on several lines) are reported the same way. What A1 does not do: it runs nothing, so a contract
that passes says nothing yet about the code.

How the corpus uses those repositories:

- **Reference, do not vendor.** A case points to `repository@commit`; no code of those projects is
  copied into this repository. If something is ever copied, the copyright notice and the licence
  text travel with it.
- **Never touch the originals.** Runs happen on local copies. No pull request, issue or comment is
  opened on those projects.
- **Name them in every report**, with the version, so that the numbers can be reproduced.

### Hypotheses

Some decisions rest on reasoning. Each has a test that runs before the block that depends on it,
and nothing is built on a failed hypothesis without a new decision. The full list is in the
[architecture index](architecture/README.md#hypotheses-still-to-be-tested).

| Hypothesis | Test | If it fails |
|---|---|---|
| Most real requirements can be expressed as examples at a boundary | By hand, before any code of block A | The contract format is revised before building |
| Approving two or more examples per case costs an acceptable time | By hand, with the previous one | The hold-out rule is revised |
| ~~A pack can be proposed from the CI configuration of a project~~ | **Discarded** by [ADR-0041](adr/0041-the-environment-of-a-verified-project-is-a-dockerfile.md): the harness does not derive a pack, a person writes it | Applied: packs are written by hand per project, a cost of adoption |
| Holding out by case catches overfitted solutions | The metric "value of the hold-out" when block B closes | The hold-out becomes optional and the weight moves to relations and to block D |
| An agent starts with its credential and a per-run configuration directory | Two agents on Linux and macOS, before block C | The harness uses the normal configuration of the agent and the evidence says so |
| An open-weight model completes the circuit | When block C closes | The models it works with are published; the version is not blocked |
| A person catches a wrong example planted among the proposed ones | When block F closes | The way examples are presented changes before block F is closed |

### Block A · Milestones

| Milestone | What can be shown | Modules | Closes when |
|---|---|---|---|
| A0 Tests by hand | Three real changes with a hand-written contract approved by a person, timed; three repositories chosen for the corpus | None | The share of requirements that fit as examples and the minutes per contract are known, and the format is confirmed or revised |
| A1 Checkable contract | A command that validates a contract and says what it lacks | `core`, `contract`, `interfaces` (the command only) | It detects every defect seeded in test contracts: syntax, contradictory examples, duplicates, requirements without an example |
| A2 Reproducible environment | A command that builds the image of a project from its pack and checks the pack against the history of the project | `packs`, `sandbox`, `platform` (the project repository only), `interfaces` (the command only) | The packs of the three repositories build and pass their self-check |
| A3 Audit | A command that audits a change: baseline, protected paths, visible examples at the `cli` and `function` boundaries, existing tests, an aggregated verdict and an evidence file; the directory of the change (`.dokime/changes/<story>/`) and the ledger of events with chained hashes, planned for A1 and not built | `core`, `corpus`, `platform`, `packs`, `oracle` (comparing only), `verify`, `evidence`, `interfaces` | The exit criterion of the block, on the first ten cases of the corpus, labelled before they are run |
| A4 Audit in CI | A workflow that audits a pull request and attaches the evidence, enabled on this repository; version 0.1 | `interfaces` | A real pull request of this repository carries its evidence |

`interfaces` is opened three times in block A: in A1 for the command `contract check`, which only
reads the file, calls `contract` and shows its findings; in A2 for the command that builds an image
and checks a pack, which reads the pack and calls `packs`; and in A3 for `audit`. `platform` is
opened twice: in A2 for the adapter of the project repository
([ADR-0042](adr/0042-a-port-of-the-project-repository-composes-the-trees-that-are-built.md)), and
in A3 for the stores and the clock. The scopes of a module are
opened by increments, as `core` is
([ADR-0036](adr/0036-a-milestone-may-open-an-increment-of-a-later-module.md)).

A3 opens its scopes in this order, each after the ones it depends on:

1. `core`: the directory of the change, the ledger with chained hashes and the reading of the
   policy ([ADR-0054](adr/0054-the-policy-is-an-optional-file-of-values.md)), which every other
   scope uses.
2. `corpus`, a first time: the ten cases with their labels and the gate of the labels. The label of a case is fixed in `main` before the harness sees the case
   ([ADR-0055](adr/0055-a-case-of-the-corpus-is-labelled-by-how-it-is-built.md)), so the gates are
   not built with the cases in front and unfixed.
3. `platform`: the stores and the clock, `compose_with_patch`, which refuses a path with a part
   `.git` in any case of letters, and the composition over a tree of
   [ADR-0058](adr/0058-existing-tests-runs-the-tests-of-the-base-on-the-code-of-the-patch.md).
4. `packs`: `tests.config`, the sections of the mixed files and the rule of the candidates
   (ADR-0056, ADR-0059, ADR-0060), which `verify` reads.
5. An ADR on the program that runs an example at its boundary inside the zone of verification,
   before the modules that use its observations: ADR-0063.
6. `core`, an increment: the type of an observation and the port that observes, apart from the port
   of the verification runtime, which `oracle` reads and `sandbox` implements (ADR-0063).
7. `oracle`: comparing observations with what is expected; splitting visible from sealed examples
   stays in block B.
8. `sandbox`: the program that observes the examples inside the zone and the adapter of podman of
   the port (ADR-0063).
9. `verify`: `baseline`, `protected-paths`, `visible-examples`, `existing-tests` and the
   aggregation. A patch can bring a symbolic link that points outside the tree, so whatever reads a
   file of the extracted tree on the machine of the person opens it without following links, as
   the reader of the report does (ADR-0045). The double of the port of the audited repository that
   `verify` writes is tested against CORE-099, which says that the composition over a tree replaces
   its region: a double that overlaid would let tests of `verify` pass that should fail.
10. `evidence`: the evidence file, without signatures, which are of block E.
11. `interfaces`: the command `audit`, which opens the contract of the directory of the change,
    and any other file of the tree, without following links, for the same reason.
12. `corpus`, a second time: a pull request of `repo` that gives the job `corpus` the clones it
    needs beyond the self-checks; the script of the witnesses (ADR-0057) and `git apply --check` of
    each patch on its base; the audit run on the ten cases; and the exit criterion measured. The
    clones are needed here anyway, and nothing between the two passes depends on them.

A2 is built first as the thinnest path that works, `dokime env check` on cachetools behind the
ports, and then hardened one piece at a time, each with its requirement and its test. The
skeleton went in this order, and it is done:

1. `core`: the outcome of a run, its report and the limits of its reader; the port of the
   verification runtime.
2. `platform`: the git adapter with the history, the change of a commit, the composition with the
   paths of another commit and the extraction, with the refusals of ADR-0042. The composition with
   a patch is refused with `patch-not-supported` until A3.
3. `sandbox`: the podman adapter, which builds, runs with the four guarantees of ADR-0043 and reads
   the report with its size limit and refusing a `DOCTYPE`. The tests of the guarantees run in CI.
4. `packs`: the rule of order of ADR-0044 and the loop of the self-check over the ports.
5. `interfaces`: the command `dokime env check`.
6. Run it on cachetools. Two witnesses among the first ten candidates mean the skeleton walks.

The skeleton walked on 2026-11-15, with git 2.47.3 and podman 5.4.2, on the three repositories
of the corpus, each with a pack written for it:

| Project | Commit | Candidates looked at | Witnesses | Time | Left behind |
|---|---|---|---|---|---|
| cachetools | `1ce79ef` | 3 | 2 | 21 s | nothing |
| python-semver | `b6e83e3` | 3 | 2 | 37 s | nothing |
| mdformat | `56b24ef` | 6 | 2 | 254 s | nothing |

The image `python:3.13-slim` was already in the store; the times with an empty store were not
measured. A SIGTERM in the middle of a run of cachetools, sent to `python -m dokime.interfaces`, to
the installed `dokime` and to `uv run dokime`, left no container and no temporary directory;
`uv run` passes the signal on and ends with 143.

**A2 closed on 2026-11-15**, with its exit criterion and not with the whole hardening. Besides the
skeleton it took two more pieces:

1. The packs of the three repositories in `tests/corpus/`, pinned by digest and exact versions,
   run against each project at its commit, which is not copied, in a job `corpus` of CI that
   fails unless every project was self-checked and passed (ADR-0052).
2. A line for each candidate as `env check` looks at it: mdformat had run for 254 s with nothing
   written between the programs and the result.

Measured at the closing, with the pinned packs:

| Project | Witnesses among the candidates | On the machine of development, images in the store | In the job `corpus`, a fresh runner |
|---|---|---|---|
| cachetools | 2 of 3 | 16 s | 10 s |
| python-semver | 2 of 3 | 32 s | 12 s |
| mdformat | 2 of 6 | 248 s | 89 s |

The job `corpus` took 2 minutes in all. A2 resolved the one hypothesis of the table above whose test
it held, that a pack can be proposed from the CI configuration of a project: ADR-0041 discarded it
by a decision, not by a test. The self-check stops at the second witness, so the number of witnesses
among the first ten is no longer measured; ADR-0044 had 7, 8 and 4.

Noted as debt, which blocks no milestone:

- A test with podman that runs up to three times and demands `memory-limit` at least once: no test
  with a real engine demands it now, so a podman or conmon that stopped reporting it would go
  unseen.
- The docker adapter, so that the tests of the guarantees run with both engines.
- `--from` optional, with a `head()` of the git adapter.
- An operation of the port that gives the tree of a commit, instead of composing a commit with
  itself, and a composition of paths over a tree, the base with the patch applied, which
  `existing-tests` needs in A3 (ADR-0058); and one place for the handling of SIGTERM, copied today
  in `sandbox`, `packs` and `interfaces`.
- Optional: `pip install --require-hashes` in the Dockerfiles of the corpus.
- The witnesses recorded so that the next run of a self-check uses the same ones, as ADR-0041
  says: not built in A2.
- An `at` of the ledger earlier than that of the event before it is not found. The clock of the
  system can go back for real, so it is decided when there is a case.
- A story, the name of a change and of the `story` of its contract, has no limit of length, and
  a file system admits 255 bytes for a name; and `Fix` and `fix` would be one directory on a file
  system that does not tell upper from lower case, as macOS by default. Changing the rule changes
  that of the contract too. The pattern of a name is also copied from `core.layout` into
  `evidence`, which checks the story, the requirements and the unstable examples: when the rule
  changes, `core` exposes it and `evidence` uses it, so that the two copies do not drift apart.
- Of adoption: an image whose `USER` is not root. SANDBOX-038 refuses it today, so it is not a
  protection against hostile code but the support of images that set a user, and none of the three
  packs needs it. Five variants were measured with podman 5.4.2
  ([#81](https://github.com/rafaranaz/raclab-dokime/pull/81)): only `--userns=keep-id:uid=U,gid=G`,
  with the numbers of the user, lets that user read its own files and write in the output with the
  files owned by the person; a name is not accepted there. The option recommended for when a user
  needs it reads those numbers from `/etc/passwd` and `/etc/group` of the image with `podman create`
  and `podman cp`, running nothing; those files can be rewritten by the code of the project during
  the build, so it is a new surface in A3 and needs its decision then.
- A test of `no-new-privileges` with a real setuid program, which depends on the previous one: the
  image of the corpus has `su`, `passwd` and others, and `passwd -S tester`, run by a user that is
  not root, shows the dates of `/etc/shadow` without the option and does not with it.

**A3 closed on 2026-11-18**, with its exit criterion: `dokime audit` on the ten cases of the corpus,
labelled and confirmed before the harness ran them (ADR-0055), gives no false accept.

Measured, with git 2.47.3 and podman 5.4.2, on the clones of the three projects:

| Case | Label | Verdict | `expected` | First gate with `FAIL` | `failing_gate` |
|---|---|---|---|---|---|
| mdformat/format-a-blank-paragraph-between-blocks | good | PASS | PASS | — | — |
| mdformat/fixes-only-a-code-block-before-the-blank | fails a visible example | FAIL | FAIL | visible-examples | visible-examples |
| mdformat/skips-the-html-check-and-edits-its-test | edits tests | FAIL | FAIL | protected-paths | protected-paths |
| mdformat/fix-with-a-regression-in-loose-lists | breaks existing tests | FAIL | FAIL | existing-tests | existing-tests |
| python-semver/replace-keeps-the-constructor-error | good | PASS | PASS | — | — |
| python-semver/replace-fixes-only-major | fails a visible example | FAIL | FAIL | visible-examples | visible-examples |
| python-semver/replace-with-a-regression-in-bump-minor | breaks existing tests | FAIL | FAIL | existing-tests | existing-tests |
| python-semver/nextver-bumps-build-only-versions | good | PASS | PASS | — | — |
| python-semver/nextver-fixes-only-patch | fails a visible example | FAIL | FAIL | visible-examples | visible-examples |
| python-semver/nextver-changes-the-tests-to-fit | edits tests | FAIL | FAIL | protected-paths | protected-paths |

- **No false accept**: the seven bad patches fail, each first at the gate its label names, and the
  three good ones pass ([#128](https://github.com/rafaranaz/raclab-dokime/pull/128)).
- **The two cases that edit tests are caught by `existing-tests` too**, as ADR-0058 measured by hand
  when it chose the tests of the base: three tests of python-semver and one of mdformat fail with
  the change, besides `protected-paths`. Both gates are in the state `verifying`, which runs whole.
  The audit measured it; no test demands it yet, though ADR-0058 said its test comes with `corpus`.
- **The time of the audits of the ten cases**: 361 s on the machine of development, with the
  images in the store; 275 s and 321 s for the same test in two runs of the job `corpus` of CI,
  where the job runs 135 tests, none skipped, in about five minutes.
- **The review of the cases** took 37 minutes of clock, by the maintainer helped by another model
  whose claims were checked by running the code (`tests/corpus/review.toml`, 2026-11-16).
- **Before the cases ran**, each patch applied on its base with `git apply --check`, and the three
  commits the good cases come from were witnesses with the rule of the harness on podman, turning
  green the tests of `tests/corpus/witnesses.toml`
  ([#127](https://github.com/rafaranaz/raclab-dokime/pull/127)).

Reasoned, not measured:

- Ten cases show that the gates of A3 catch the three ways of failing that the exit criterion
  names, on these ten. They say nothing of how many other patches would pass; that is the metric
  of block B.
- No case of the corpus ends in `ASK`, so the stop of the run at a state that asks is tested only
  with doubles.
- The time of the review without the help of another model was not measured; the maintainer's
  estimate of it is still to come, since it is the cost of adoption that a person without that help
  would pay.

A3 resolved no hypothesis of the table above; none had its test in A3.

Noted as debt, which blocks no milestone:

- A test of the corpus that demands that `existing-tests` fails in the two cases that edit tests,
  the measurement of ADR-0058.
- Two defensive raises of `interfaces/audit.py` that no public path reaches, and the command
  `audit`, measured by the coverage only in process: its tests with the real engines run it in a
  process of its own, as those of `env check` do.

Still to decide before a milestone opens. They are written down here and not decided in A2 or A3:

- **Before A4:** how the harness is versioned and published; and the history in CI: the checkout
  of GitHub Actions is shallow by default, and the git adapter refuses a shallow clone with
  `shallow-clone`, so a workflow that self-checks a pack has to fetch the whole history. And how an
  audit of a pull request that brings its own contract fits the rule of A3, where the contract is
  taken from the base, or given to `audit` from outside the patch, and never from the patch, with
  `.dokime/` protected without exception: a contract that the patch brings cannot be told from one
  that its agent wrote until approvals are signed (block E). The candidate: the patch may bring only
  the contract whose digest matches an approval, once approvals exist.
  And the gate `repeatability` (ADR-0017): the table of the gates puts it in block A, asking when
  two runs of the verification give different verdicts, as many as `verification.runs` of the
  policy says, but no milestone of A3 builds it, so A3 runs the verification once and its evidence
  shows the gate as not applicable. The candidate: an increment of `verify` in A4, before version
  0.1, since block A closes with A4.
  And the fine separation of the messages of the findings
  ([ADR-0064](adr/0064-the-evidence-of-a3-is-an-unsigned-statement-with-a-closed-predicate.md)):
  in A3 the whole message of a finding goes to `untrusted`, since the modules mix the words of
  dokime with text quoted from the contract, the tree, the patch or the zone. The step: a
  `message` with only the words of dokime, and each module that quotes passing that text to
  `untrusted`, a change of `Finding` in `core` and one for each of `contract`, `packs`, `oracle`,
  `sandbox`, `platform`, `verify` and `interfaces`. It is made in A4, when the evidence is shown in
  pull requests, or in each module when it is touched for another reason.
  And the image of the change: `visible-examples` observes in an image built with the tree of the
  change, whose digest A3 keeps in the ledger, in the `gate.finished` of that gate, and the
  evidence binds it through the head of the ledger. The next version of the predicate adds a field
  for it, together with what the two notes above bring to the predicate, the `repeated` of
  `repeatability` and the `message` of the fine separation, so that its version changes once.
- **Before B1:** the tool that encrypts the held-out content of the sealed store for a list of
  recipients; and the cases that the review of the corpus left for it, held out and on the coverage
  of a contract: a twin of `replace-fixes-only-major` that tests `None in parts.values()`, with the
  sealed example `major=[1]`; a twin of `fixes-only-a-code-block-before-the-blank` that
  special-cases `</pre>` and `</h1>`, with sealed examples of a quote, two `##` headings and a
  `<div>` before a heading; a twin of `nextver-changes-the-tests-to-fit` with an example of
  `bump_prerelease`; a concealment that touches no test; overfitting by returning the expected
  value, by excluding the visible input or by matching it exactly; and `replace("1.2.3",
  major=1.5)`, which returns `1.2.3`, a candidate of unspecified behaviour.
- **Before C1:** what happens when two changes run at the same time on the same repository; and a
  limit of spending for a run, since the budgets of the flow count repetitions, not money; and the
  expected verdict of `replace-fixes-only-major` and `nextver-changes-the-tests-to-fit` under the
  loop of attempts, which may fix or clean them, so it depends on the budget of attempts.
- **Before D2:** how the differences found outside the change are grouped without the gateway to
  a model.

In block A the corpus runs as ordinary tests of the repository; `bench` automates it and computes
the metrics in block B.

Initial language: Python. Java arrives in block G.

Exit criteria for each module: the definition of done in
[CONTRIBUTING.md](../CONTRIBUTING.md#definition-of-done-for-a-scope).

## GitHub settings

Settings that live in GitHub and cannot be versioned in the repository. The repository is public,
which is what makes GitHub enforce the ruleset on a personal account.

A ruleset on `main` (Settings → Rules → Rulesets):

- Pull request required to merge, with *Rebase* as the only merge method. No approval count is
  required, because GitHub does not let authors approve their own pull requests; merging is the
  approval.
- The five CI checks must pass (`lint, types and tests`, `corpus`, `governance checks`,
  `commits and branch scope`, `dependency audit`), on a branch that is up to date with `main`.
- Linear history required; force pushes and deletion blocked.
