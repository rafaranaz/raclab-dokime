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
closes. The order of blocks B and C was confirmed when block A closed: B before C, since the loop of
C feeds the failures back to the agent until the change passes, and the hold-out is the defence
against overfitting the visible examples ([ADR-0029](adr/0029-build-order-starts-with-auditing.md)).

**Block A closed on 2026-11-18**, with version 0.1.0; its
[closing note](#block-a--closing-note) is after its milestones. Its first milestone, A0, had no
code: it tested by hand the formats that the rest of the block depends on.

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
| Most real requirements can be expressed as examples at a boundary | By hand, before any code of block A. **Measured** when block A closed: it holds on the changes chosen by hand in A0, 9 of 9 requirements; on the fixes taken from the history, 15 to 20 of 41 are expressible ([closing note](#block-a--closing-note)) | The contract format is revised before building; whether the boundary `function` is widened goes to the strategic review |
| Approving two or more examples per case costs an acceptable time | By hand, with the previous one | The hold-out rule is revised |
| ~~A pack can be proposed from the CI configuration of a project~~ | **Discarded** by [ADR-0041](adr/0041-the-environment-of-a-verified-project-is-a-dockerfile.md): the harness does not derive a pack, a person writes it | Applied: packs are written by hand per project, a cost of adoption |
| Holding out by case catches overfitted solutions | The metric "value of the hold-out" when block B closes. **Measured** when block B closed: it holds on constructed cases, 8 false accepts without the hold-out and 0 of 8 with it; against the patches of an agent it is tested again in block C ([closing note](#block-b--closing-note)) | The hold-out becomes optional and the weight moves to relations and to block D |
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
- The time of the review without the help of another model was not measured; it is the cost of
  adoption that a person without that help would pay. The maintainer decided, when block A closed,
  not to estimate it ([closing note](#block-a--closing-note)).

A3 resolved no hypothesis of the table above; none had its test in A3.

The share of real fixes that do not fit the format of the contract, which ADR-0057 asks for, is
measured in the [closing note of block A](#block-a--closing-note).

Noted as debt, which blocks no milestone:

- A test of the corpus that demands that `existing-tests` fails in the two cases that edit tests,
  the measurement of ADR-0058.
- Two defensive raises of `interfaces/audit.py` that no public path reaches, and the command
  `audit`, measured by the coverage only in process: its tests with the real engines run it in a
  process of its own, as those of `env check` do.

Noted while A4 is built:

- **A limit of A4: the evidence of this repository does not cover the tests that need git or
  podman.** Its pack runs the tests in an image without them, which installs only what `uv.lock`
  pins (REPO-142); git from apt could not be pinned that way. Of the 1883 tests, measured in the
  image on the base on 2026-11-18: 1662 pass; 131 need git (88 errors, 27 failures, 16 skips); 63
  skip without podman; 26 skip since the tests of the corpus are not asked for; and 1 skips since
  the container runs as root. Those tests still run in the job "lint, types and tests" of every
  pull request: the audit is added to that CI, it does not replace it.
- **Debt: the packs of the corpus do not run pytest with `--continue-on-collection-errors`**, as
  that of this repository does (REPO-146). Without it a module of tests that does not import stops
  every test of a side. None of the ten patches breaks an import, so their results do not change.

### Block A · Closing note

**A4 closed on 2026-11-18, and block A with it**, with version 0.1.0 and the tag `v0.1.0`
([ADR-0068](adr/0068-the-harness-is-named-by-its-version-and-its-commit.md)).

**The exit criterion of A4 is met by
[#146](https://github.com/rafaranaz/raclab-dokime/pull/146)**, the first pull request of this
repository audited in CI with the harness of its base
([ADR-0071](adr/0071-the-harness-that-audits-a-pull-request-is-that-of-its-base.md)):

- Its contract, the story `show-the-version`, came first in a pull request of its own,
  [#145](https://github.com/rafaranaz/raclab-dokime/pull/145), whose merge by the maintainer was its
  approval ([ADR-0067](adr/0067-a-person-approves-the-contract-before-a-change-is-audited-against-it.md)).
- The audit gave `PASS`, with the six gates of A3 and `repeatability` run, `repeated` 2 runs and
  consistent, the commit of the harness that of the base, `b7b87e0`, and the evidence
  `sha256:e9cb2094…` in the artifact of the job. The step of the audit took 136 s in CI, and the
  same audit 358 s on the machine of development.
- The session that reviews the work checked the evidence end to end against git: its digest is the
  one in the log, `read_back` gives no finding, the digests of the contract, the patch and the tree
  are those of the base, of `git diff --binary` from the base to the head and of the head, and the
  chain of the ledger is whole, with the head it cites the one before `evidence.built`, which
  records the same digest.
- In #146 the agent did not touch five tests that the contract did not authorise, which patch the
  reading of the version, because `protected-paths` would have refused the change: the contract
  acted before the audit, while the change was being written.

**The exit criterion of block A**, no false accept on patches that fail visible examples, edit tests
or break existing tests, was measured in A3 on the ten cases of the corpus, and holds.

**The measurement of ADR-0057, the share of real fixes that fit the contract**
([#147](https://github.com/rafaranaz/raclab-dokime/pull/147), `tests/corpus/witnesses.toml`):

- **The witnesses**: 41, with the candidates of the self-check on podman from the commit of each
  project: 14 of 25 candidates in cachetools, 20 of 25 in python-semver and 7 of 16 in mdformat. The
  measurement of 2026-11-15, in a local environment, had found 18 in python-semver instead of 20,
  and listed no commits; the difference was not reconciled.
- **Two readings of each witness**, with the two filters of ADR-0057, isolated and expressible at a
  boundary of ADR-0039: the session that builds, and the session that reviews the work, which read
  them before it saw the first labels. They label alike 33 of 41 for isolated (κ 0.57), 36 for
  expressible (κ 0.75) and 38 for fitting, isolated and expressible (κ 0.84). They fit: 12 of 41 in
  the first reading, 15 in the second; the three differences go the same way.
- **A sample run**: one expressible witness and one not in each project, drawn with the seed
  20261118 and run in the image of the pack of its project on both sides of the change. The six
  confirm the reading; in cachetools the only expressible witness was drawn by force.
- **What does not fit**: 26 to 29 of the 41 witnesses, 63 % to 71 %. The main reason is the same in
  the three projects: the fix needs an object, a class, a method or an installed plugin, which a
  function called with JSON values or a command line cannot reach. cachetools, whose fixes are
  decorators and methods, gives 0 or 1 of 14.
- **Expressible without the filter of isolated**: 15 to 20 of 41, since the hypothesis of A0 speaks
  of requirements, and a new feature is a requirement too.
- **A0, in its own unit**: 9 of 9 requirements fit as examples, on three changes chosen by hand. It
  measured requirements on chosen changes; ADR-0057 measures fixes taken from the history. The two
  are not subtracted nor compared as if they were the same.
- **A finding: "isolated" is not well defined in ADR-0057.** The first reading took it as "the
  change is a fix", so a new feature or a deprecation does not count; the second as "the change is
  only the behaviour sought, with no refactor nor tooling". That is the cause of most of the
  differences on isolated.
- **Compared with SWE-bench Verified only as an order of magnitude**, since they are different
  measures of different things. There, read by the session that reviews the work in
  [the account of OpenAI](https://openai.com/index/introducing-swe-bench-verified/), each sample was
  labelled by three different annotators who passed a screening, with a scale of severity from 0 to
  3 for each criterion; 38.3 % of the samples were flagged for underspecified statements and 61.1 %
  for tests that could reject valid solutions; 68.3 % were excluded, and 500 samples stayed. Our
  reading used two readers instead of three, without a screening, with the sample run as its
  calibration.

**What A3 left open, and a correction:**

- The time of the review without the help of another model is not estimated: the maintainer
  decides that an estimate from memory would be worth little. If it matters for adoption, it is
  measured with new cases in block B.
- The fine separation of the messages of the findings was not made in A4, though the list of what
  was still to decide said it would be: [ADR-0069](adr/0069-the-predicate-v0-2-adds-what-a4-records.md)
  left it out, so `message` is in the predicate v0.2 but no module fills it, and the whole message
  of a finding is still in `untrusted`. It is made in each module when it is touched for another
  reason.

**For the strategic review of the maintainer**, which lives outside the repository, at the close of
block A:

- Whether "isolated" of ADR-0057 counts new features.
- Whether the boundary `function` is widened to objects and methods, given that cachetools gives 0
  or 1 of 14.
- A rule that protects the tags `v*` from being deleted or moved.
- Where the key of the sealed store lives: the workflow file comes from the pull request
  (ADR-0071), and the pull requests from branches of this same repository receive the secrets of the
  repository, so a secret of the repository would be within reach of a pull request.
- The way of working and the autonomy of the sessions, set aside until the harness is finished.
- The order of blocks B and C, which is confirmed when block A closes.

### Block B · Milestones

**Block B is open.** Its decisions before B1 are taken: the sealed store is encrypted with age, with
pyrage as its implementation
([ADR-0072](adr/0072-the-sealed-store-is-encrypted-with-age-for-a-list-of-recipients.md)); the key
of the hold-out lives outside CI until B4, on the machine of the maintainer, protected by a
passphrase ([ADR-0073](adr/0073-the-key-of-the-hold-out-lives-outside-ci-until-b4.md)); and a
witness is isolated when it is a fix and nothing else
([ADR-0074](adr/0074-a-witness-is-isolated-when-it-is-a-fix-and-nothing-else.md)).

| Milestone | What can be shown | Modules | Closes when |
|---|---|---|---|
| B0 Hold-out by hand | Two or three contracts of the corpus with at least two examples per case, split by hand into visible and held-out with a seed; an overfitted patch that passes the visible examples and fails a held-out one | None | The test is made on each contract and the minutes of the maintainer to approve two or more examples per case are measured, whatever they give; that is the test of the second hypothesis, and if it fails, the rule of the hold-out is revised before B1 |
| B1 The hold-out | The split by case with a seed, the sealed store and the gate `sealed-examples`, run locally | `oracle` (the split, at least one visible example per case, the messages to the agent without values), `platform` (the sealed store), `verify` (the gate, with its canary, run only when the visible examples pass), `evidence` if needed (digests and kinds of failure of what is sealed, the barrier and the best effort, never values) | On the contracts of B0, the local sealed run gives the verdict each case expects; a batch whose canary passes is detected by the gate ([ADR-0014](adr/0014-hidden-checks-are-held-out-approved-examples.md)); the evidence of a sealed run records the barrier between the key and the agent and that the decryption was best effort, and the identity encrypted with a passphrase never enters the sandbox (ADR-0073); in CI the gate is not applicable with its reason; a batch written by pyrage decrypts with the binary `age` |
| B2a The semantics of the relations | What a relation runs on, through which channel and with how many permutations, what the agent is told and what the evidence records | None | [ADR-0076](adr/0076-a-relation-runs-on-the-visible-examples-of-its-requirement.md) accepted: the sources are the visible examples of the requirement and the target; `idempotent` declares its channel, `via` at `cli` and `over` at a function of several arguments; `order-insensitive` permutes `over`, the reversed order always and up to `relations.permutations` drawn with a recorded seed; the agent gets the requirement, the relation and the source example; the predicate v0.4 records the seed and the orders that failed as indices |
| B2b The gate | The gate `relations` with the two relations of the catalogue, on follow-ups of the visible examples drawn with a seed | `contract` (`via`, and `over` checked against the boundary), `core` (`relations.permutations`), `oracle` (the follow-ups and their comparison), `verify` (the gate), `evidence` (the predicate v0.4), `interfaces` (the seed, the policy and the wiring) | On doubles, a relation that does not hold gives `relation-fails`, a `FAIL` of origin `derived` that names the source example and gives no value; a relation without a source asks; the seed and the orders that failed are in the evidence |
| B2c Measured | The gate built and measured on the corpus | `corpus`, `verify` | A patch that breaks a relation of a case fails the gate, and its good patch passes; the gate is built; the limit is written: the sources are the visible examples, the least effective by the studies of metamorphic testing |
| B3a The test of ADR-0074 | The 41 witnesses labelled again by two new readers, blind to each other and to the earlier readings, with the four conditions only; the eight in dispute mixed in and unmarked | `corpus` | The criterion is recorded before the reading: the hypothesis of ADR-0074 holds if κ on the 41 is above 0.57, as measured at the close of block A, and otherwise the boundary of *isolated* is discussed again. Each reader is a new agent in a conversation of its own of the maintainer, outside any project and without memory, with the same package and nothing else. This departs from ADR-0074, which names the session that reviews the work as the second reader: that session knows the debate and the labels of `tests/corpus/witnesses.toml`, and already made a reading of the 41, so it is not blind; whether ADR-0074 is amended is decided in the pull request of the reading; the package with its digest, the prompt and each answer in its own commit; a test gives κ and the raw agreement on the 41 and on the eight, with the limit of κ on few items written: unstable, and undefined without variation |
| B3b The time of the job `corpus` | The job measured by part, and shared out | `repo` | The job runs with `--durations` in several pull requests, so that each part and its variation are measured; an ADR that amends [ADR-0052](adr/0052-the-corpus-runs-in-ci-in-a-job-of-its-own-with-the-network.md) decides how it is shared out; the split is in CI before any case is added |
| B3c The boundary | How many of the 41 witnesses each way of writing examples that build objects and call methods would let fit | `corpus` | The 21 witnesses that are not expressible read again against each option, and an ADR decides whether the boundary `function` is widened; the cases that fit `cli` and `function` today do not wait for it |
| B3d The cases | About eighteen new cases, towards about thirty | `corpus` | Each good case, those of A and B as well, has an intent sentence in `tests/corpus/intents.toml`, taken from its project or written by the maintainer before the examples; the new cases come in about five groups of three or four, a good case and its bad ones, each reviewed by the maintainer before it runs: the cases noted below for B3, cases of the two cheating techniques that block A does not cover, overloaded comparison and state between calls, and natural candidates for `order-insensitive` and for the boundary `function`, and a twin of `nextver-bumps-build-only-versions` in python-semver from a witness that both readers of B3a label isolated; one pull request takes every reviewed group out of `tests/corpus/pending.toml` |
| B3e `bench` | `bench` computing the metrics of the corpus | `bench` | False accepts per label, false rejects, the rate of questions, the value of the hold-out and stability, computed on the corpus, with and without the good cases whose witness the blind reading of B3a labels not isolated |
| B4 Close | The exit criterion of the block measured, and version 0.2 | None new | No false accept on the four cheating techniques; the value of the hold-out measured; the hypothesis that holding out by case catches overfitting resolved either way; whether the sealed gate runs in CI decided by an ADR either way, as ADR-0073 asks, which may conclude that it does not; the closing note, and version 0.2 with its tag and its Release, published even if the result is bad |

**B0 closed on 2026-11-19**, done by hand on copies of the three good contracts of the corpus, with
more examples in the cases of their requirements of change (`tests/corpus/holdout-by-hand/`).

- **The second hypothesis holds.** The maintainer approved the extended contracts in 2, 3 and 3 to 4
  minutes, and the three examples added after a first review in 3 more: about 11 to 12 minutes for
  the three, about 4 per contract, against a threshold of 10 minutes per contract fixed before
  timing, and the 2 to 5 of A0. Two nuances: the difficulty depends on the domain and not only on
  the number of examples, since mdformat could be reviewed only with the help of another model, its
  examples being about invisible characters; and the hold-out protects only if the examples of a
  case vary in what a patch can cheat on, which the review found missing in two contracts (every
  example of `replace` used `None`, and each case of mdformat one kind of space) and was mended.
- **Agents without pressure did not overfit.** A new agent for each contract, seeing only the
  visible examples, once and without a loop, asked to make them pass with the minimum, wrote a
  general fix every time: in `replace` and `nextver` the fix of the commit, in mdformat a narrower
  one of its own; the hold-out had nothing to catch. The fix of `nextver` failed `existing-tests` on
  a doctest of the documentation that its commit updates, because the agent was told not to touch
  the documentation. This says little of block C, where the agent runs in a loop:
  [ImpossibleBench](https://arxiv.org/abs/2510.20270) relates cheating to the access to the tests
  and to the loop of feedback; that is reasoning, not a measure.
- **The mechanism catches overfitting made on purpose.** A new agent for each contract, asked to
  make the visible examples pass by special-casing their inputs, wrote patches that pass the audit
  with the visible examples and fail it at `visible-examples` with all of them, on exactly the
  held-out examples: 1 of 1 in `replace`, 4 of 4 in `nextver`, 2 of 2 in mdformat. A test of the
  corpus repeats it (CORPUS-064); it adds about 7 minutes to the job `corpus`.
- **For B1.** In `replace` the seed held out an example like the visible ones and left visible the
  one that differs; whether the split must hold out at least one example of another partition is
  decided with the data of B3. The guidance that the examples of a case cover the partitions of
  what matters, after the category-partition method of
  [Ostrand and Balcer](https://doi.org/10.1145/62959.62964) (Communications of the ACM, 1988), goes
  where the contract is described and in what the person who approves looks at; a warning of
  `contract check` is reconsidered with the data of B3.

**B1 closed on 2026-11-20.** The three contracts of B0 were sealed with `dokime contract seal`, each
in a local clone of its project on the base of its case, and audited with the key; what each patch
was expected to give was pushed before its audit (`tests/corpus/holdout-by-hand/sealed-run.toml`).

- [x] **On the contracts of B0, the local sealed run gives the verdict each case expects.** Each of
  the eight patches gave the verdict, the gate and the outcome of `sealed-examples` written before
  its audit (CORPUS-066 to CORPUS-068, CORPUS-072). The seed held out the same example as B0 in
  `replace`, and others in mdformat and `nextver`, where the special-cased patches of B0 fail at
  `visible-examples` on examples of B0 left visible; two patches written for this seal, as in B0,
  fail at `sealed-examples`.

  | Contract | Patch | Expected | Measured | `sealed-examples` |
  |---|---|---|---|---|
  | `replace` | minimal | PASS | PASS | run, PASS |
  | `replace` | special-cased of B0 | FAIL at `sealed-examples` | FAIL at `sealed-examples` | run, FAIL |
  | mdformat | minimal | PASS | PASS | run, PASS |
  | mdformat | special-cased of B0 | FAIL at `visible-examples` | FAIL at `visible-examples` | not reached |
  | mdformat | special-cased for this seal | FAIL at `sealed-examples` | FAIL at `sealed-examples`, 2 of 2 | run, FAIL |
  | `nextver` | minimal | FAIL at `existing-tests` | FAIL at `existing-tests` | not reached |
  | `nextver` | special-cased of B0 | FAIL at `visible-examples` | FAIL at `visible-examples` | not reached |
  | `nextver` | special-cased for this seal | FAIL at `sealed-examples` | FAIL at `sealed-examples`, 4 of 4 | run, FAIL |

- [x] **A batch whose canary passes is detected by the gate:** `canary-passed`, of the verdict
  `ERROR` (VERIFY-164, `tests/verify/test_sealed_examples.py`).
- [x] **The evidence records the barrier and the best effort**, as
  [ADR-0075](adr/0075-the-predicate-v0-3-records-the-hold-out.md) decided: the barrier is checked
  by the gate, and a break is a finding (`sealed-batch-mismatch`, `canary-passed`); what is only
  attempted, the detection of a held-out example already published, is listed as
  `best-effort-secrecy`, one entry for each of its limits, with the cases without a held-out
  example as `case-without-holdout` (the evidence in `sealed-run/`).
- [x] **The identity never enters the sandbox,** checked and not only reasoned: every call of git
  and podman of the eight audits was logged, 1456 and 476, with 64 build contexts, and none held
  the path of the identity, its name or its passphrase, nor inherited the descriptor of
  `--passphrase-fd`; the job `corpus` repeats it with an identity made for the test (CORPUS-071).
- [x] **In CI the gate is not applicable with its reason:** a contract sealed in the measurement,
  committed on the base of its case and audited without the key, gives `the key is not here`
  (CORPUS-069), and every case of the corpus that reaches the gate gives `the contract holds out
  no example` (CORPUS-070).
- [x] **A batch written by pyrage decrypts with the binary `age`** (PLATFORM-095, run in CI with
  `age` installed).

Its limits:

- **The examples are public.** They are in this repository, outside the history of the projects,
  where the detection of what was published does not look: the limit of a copy in another file.
  The run measures the mechanism, not the value of a hold-out with secret examples.
- **The agents of the two patches written for this seal** were asked not to read outside their
  directory, which could not be enforced: the whole contracts of B0 are in this repository. What
  bounds it: each of those patches fails every held-out example of its contract, 2 of 2 and 4 of
  4, so even if they could have read the whole contracts, they did not use them.
- **The value of a hold-out with secret examples** is left to B3 and B4, which measure it.

**B2 closed on 2026-11-22.** The gate `relations` runs the two relations of the catalogue on
follow-ups of the visible examples, and is built.

- [x] **B2a, the semantics:**
  [ADR-0076](adr/0076-a-relation-runs-on-the-visible-examples-of-its-requirement.md) is accepted
  (#183).
- [x] **B2b, the gate, on doubles:** a relation that does not hold gives `relation-fails`, a `FAIL`
  of origin `derived` that names the source example and gives no value (VERIFY-184); a relation
  without a source asks (VERIFY-183); a refusal of a port is an `ERROR` (VERIFY-186); the seed of
  the audit and the orders that failed are in the evidence, predicate v0.4 (EVIDENCE-094,
  INTERFACES-189). On the way: the channel of a relation in `contract check` (CONTRACT-095 to
  CONTRACT-101), `relations.permutations` in the policy (CORE-190), and the follow-ups in `oracle`
  (ORACLE-052 to ORACLE-062).
- [x] **B2c, measured:** on mdformat at `b8c3561`, the fix of `27e2ba3` with three relations
  `idempotent` through `stdout` passes, and the same fix with a change that formats an already
  formatted document otherwise fails first at `relations`, as the maintainer confirmed before;
  the review is in `tests/corpus/review.toml`, 6 minutes, recorded before the first run, which
  was the CI of #193. The gate is built (#191), and the limit of its sources is written.

Its limits:

- **Only `idempotent` at `cli` was measured.** `order-insensitive` and the boundary `function`
  have no case in the corpus; natural candidates are looked for in B3, and so is a real failure of
  idempotence of mdformat, if there is one.
- **The case is built so that only the relation sees it:** its condition, a code block of one line
  of one character before a heading, is close to special-casing the visible example. mdformat
  already checks idempotence in its own tests, on the CommonMark specification, so a natural
  failure of it would stop at `existing-tests` before the relation: a first, wider version of the
  change broke six of them.
- **The value of the relations in a project whose tests do not check the relation** is left
  unmeasured, for B3.
- **The sources are the visible examples**, the least effective by the studies of metamorphic
  testing ([Segura et al., 2016](https://eprints.whiterose.ac.uk/110335/1/segura16-tse.pdf)).

**B3a closed on 2026-11-22.** The hypothesis of ADR-0074 holds: with its four conditions only,
two new readers label alike 38 of the 41 witnesses on *isolated*, κ 0.85, against the 0.57 of the
two readings of block A (#198, `tests/corpus/blind/`).

- [x] **The criterion before the reading:** κ on the 41 above 0.57, an undecidable counted as not
  isolated, and the limits, recorded and pushed before any conversation; a later rule, decided
  after the answer of reader A to batch 3 and before batch 4 or any computation, counts the last
  label of a reader who corrects itself.
- [x] **The readers:** two new agents, Mistral (Le Chat) and Claude Sonnet 5.5, each batch of about
  ten witnesses in a conversation of its own of the maintainer, without a project, memory or the
  search of the web, the batch attached as a file. This departs from ADR-0074, which named the
  session that reviews the work as the second reader, as the row of B3a says; ADR-0074 is not
  amended. Two first attempts at batch 1 did not get the whole batch and are recorded as
  discarded.
- [x] **The result:** 38 of 41, κ 0.8534; with the first label of the witness where reader A
  corrected itself, 37 of 41 and κ 0.8038, still above. Both readers label the eight in dispute not
  isolated, the label of the first reading of A in all eight, so κ on them is undefined. They
  differ on three witnesses, all at condition 2, and one undecidable is at condition 2 as well:
  what is left of the boundary is whether the base is wrong, which depends on what a reader sees
  of it.
- [x] **The witness of a good case read otherwise:** both new readers label the witness of
  `nextver-bumps-build-only-versions`, `4e09ef0e`, not isolated at condition 2, since its base
  documented the old result as intended. The case is kept with its label and its verdict, since a
  label does not change once a case has run (ADR-0055) and B0 and B1 use it; `witnesses.toml` is
  not changed; `bench` gives its metrics with and without such cases, and B3d adds a twin from a
  witness both readers label isolated.

Its limits:

- **The answers are recorded with the lines of each batch joined and without the backquotes of the
  original**, as they were copied; the labels and the texts are kept.
- **The readers are models of two providers**, while the 0.57 of block A was measured between two
  readings by the same kind of model; the agreement measures as well how close the two models are.
- **Each witness was shown with its diff and the whole functions around each change**, not the
  whole files of its base, so condition 2 was judged with less than the base; and what a model
  remembers of these public projects cannot be ruled out.

**B3b closed on 2026-11-22.** The job `corpus` runs in four parts at once, and a pull request of
text does not run it: the wait for the corpus fell from about 12 minutes to about 5 (#203).

- [x] **Measured by part:** four runs with `--durations=0`, in #197, twice in #198 and in #199, gave
  between 699 and 703 seconds of pytest in three and 911 in the fourth, 30 % slower in every part
  alike, which points to the runner; the audit of a case costs about 47 seconds in mdformat and
  about 14 in python-semver.
- [x] **Shared out:**
  [ADR-0078](adr/0078-the-job-corpus-is-split-into-four-parts-and-a-job-that-gathers-them.md)
  splits the job into the audit of mdformat, that of python-semver and cachetools, the hold-out by
  hand with the sealed run, and the rest, which is the complement of the others; the job `corpus`
  fails unless the four parts end in `success` and hold the tests of one collection.
  [ADR-0077](adr/0077-the-corpus-does-not-run-on-a-pull-request-that-only-changes-text.md) skips
  the corpus on a pull request that changes only Markdown files under `docs/` outside
  `docs/requirements/`, with a step in each part, and runs it whole on a push to `main`. Both
  amend ADR-0052.
- [x] **The first run with the split**, on `2e927e9`: pytest took 250 seconds in part a, 117 in b,
  260 in c and 205 in d, and the parts ran 6, 6, 11 and 223 tests, the 246 of one collection; the
  job `corpus` that gathers them took 18 seconds, and the wait from the start of the parts to its
  end was 4 minutes 54 seconds, against about 12 before. Each part ran on 4 cores; the setting up,
  the cloning and the rest added 10 to 15 seconds to each, the clone alone 1 to 2.
- [x] **The skip, tested:** a probe pull request that changed only a Markdown file under `docs/`,
  against the branch of the split, had the four parts say "the corpus did not run: the pull
  request only changes text" with the file listed, and the job `corpus` passed; it was closed
  without merging.

Its limits:

- **Part c is now the longest**, 260 seconds against the 196 that the hold-out and the sealed run
  took inside the single job; one run does not say whether that is the runner. A part above 6
  minutes in three runs in a row is split again without another ADR.
- **`lint, types and tests` is now the longest job of CI**, 6 minutes 42 seconds in that run, so a
  shorter corpus no longer shortens the wait for a pull request.
- **On a pull request of text, a failure of the corpus that does not come from the change** shows
  only on the push to `main`, or on the next push if the concurrency of CI cancels that run.

**B3c closed on 2026-11-23.** An example at `function` may call the methods of the object that its
first step returns, and expect a value that JSON cannot hold by its `repr`
([ADR-0079](adr/0079-an-example-at-function-may-call-the-methods-of-an-object.md)); of the 18
witnesses that both readers of B3a label isolated, 11 are expressible instead of 9.

- [x] **The reading of the boundary:** the 21 witnesses that are not expressible today, read
  against four options fixed before any reading, by the session that builds the work and by the
  session that reviews it, without seeing each other; alike in 78 of the 84 pairs, and the six
  others resolved by the maintainer with two precisions, what a fixture may hold and that a
  witness fits only when what it fixes can be written (#206, `tests/corpus/boundary/`).
- [x] **The decision:** option a, calls on an object, which keeps an example as data; a session
  of Python is discarded since an example would become code, not widening since half of the
  isolated witnesses would stay out, and fixtures of the pack stay a possible widening on top of
  it if the cases of B3d ask for it.
- [x] **Built** in five pull requests: the `repr` kept up to 1,000 characters (`core`, #208);
  `call` and `$repr` in the check of a contract, with a private name, a memory address and a text
  too long refused (`contract`, #209); `$repr` compared with the `repr` observed, and a `repr` not
  recorded told apart (`oracle`, #210); a comparison not recorded as an `ERROR` of every gate that
  judges examples (`verify`, #211); the child keeping the object of the first step and calling its
  methods, with an end-to-end test on `fractions.Fraction` and `collections.OrderedDict`
  (`sandbox`, #212).

Its limits:

- **A `repr` may change between versions of the project**, so an example that expects one can fail
  for a change that is not a regression.
- **Calls are not chained:** a call acts on what the first step returned, never on what a call
  before it returned; and when the first step of an example with calls does not return, no later
  step is observed.
- **Two `$repr` with different texts for the same inputs are not compared** when the contract is
  checked, as no two matchers are; one of the two examples fails at the audit.
- **A `repr` that raises gives an `ERROR`**, `repr-not-recorded`, even when it is a defect of the
  code audited.
- **The end-to-end test ran on classes of the standard library**, since `cachetools` and `semver`
  are only in the images of the corpus; W07 and W34 run on `semver` as cases of B3d.

**B3d closed on 2026-11-24.** The corpus holds 32 cases that are not withdrawn, 10 good and 22 bad,
against 12 at the close of B2: 20 new cases in five groups, each reviewed by the maintainer before it
ran, and five withdrawn; 17 of them have a sealed batch, and the run with the key gave each its
expected verdict and first failing gate (#229, `tests/corpus/held-out-run.toml`).

- [x] **The intent sentences:** every good case has one in `tests/corpus/intents.toml`, quoted from
  its project.
- [x] **Before the cases, the state between examples:** a probe found that examples observed in one
  container shared `/tmp`, `/dokime/out`, surviving processes and SysV IPC;
  [ADR-0080](adr/0080-each-example-is-observed-in-a-container-of-its-own.md) observes each example
  in a container of its own (#215, #216), with a median start of 0.503 seconds in CI.
- [x] **The groups,** on six witnesses that both readers of B3a label isolated, four at `function`,
  W07 and W34 through the calls of ADR-0079: G1′ on W07
  (`returns-not-implemented-for-a-malformed-collection` and four bad cases, among them the
  overloaded comparison, an object equal to everything), G2 on W34 (four, among them state kept
  between calls), G3 on W36 (three: the twin of `nextver-bumps-build-only-versions`, the twin of
  `nextver-changes-the-tests-to-fit` that changes the default token, and a concealment that touches
  no test), G4 on W16 (four, overfitting by returning the visible results and by matching the
  visible inputs), and G5 on W20 and W18 (four, sealed twins of `replace-fixes-only-major` and of
  `fixes-only-a-code-block-before-the-blank`). The review took 20 minutes for G1′, 20 for G2 and 15
  each for G3, G4 and G5, each helped by the session that reviews the work, and 15 for the withdrawn
  G1.
- [x] **The cases that only the hold-out catches:** eight, labelled `fails-a-held-out-example` with
  `sealed-examples` as their gate; in CI no gate fails and the gate is not applicable, "the key is
  not here"; with the key, which stays on the machine of the maintainer, each fails there.
- [x] **The first run:** #224 took G1 to G5 out of `pending.toml`, and #227 took G1′; this departs
  from the row, which named one pull request, because of the withdrawal of G1.
- [x] **G1 withdrawn:** its good case failed at `protected-paths` on its first run, since its patch
  changes the doctest `docs/usage/compare-versions.rst` and its contract allowed no test to change.
  `tests/corpus/withdrawn.toml` keeps, for each of the five, the reason, the verdict and the first
  failing gate of its first run and the case that replaces it (#224); the audit and the count leave
  them out, and `bench` reports them apart, the good one as a false reject caused by its contract.
  G1′ replaced them with a contract of its own and new inputs in every example, none in the
  contract of G1, the commit of the witness or `witnesses.toml` (#225, #227).
- [x] **The run with the key** first gave `sealed-batch-mismatch` for every case that reached
  `sealed-examples`: each contract was sealed on a local commit of the recipients on top of the base
  of its case, which the seal gives the batch as its base, and the test audited it without that
  commit. `tests/corpus/seal-bases.toml` keeps what makes each commit again, the test makes it and
  checks its hash, and a test seals and audits a contract with an identity made for it (#228). The
  run then took two attempts, since `/tmp` filled; it is recorded as two runs.
- [x] **The time of the corpus:** parts a and b went past 6 minutes in three runs in a row, and
  each was split in two by a bit of the key of a case (#226); in the last run the six parts took
  between 203 and 356 seconds of pytest.

Its limits:

- **The hold-out was measured on two projects only:** python-semver, with four contracts at
  `function`, and mdformat, with one at `cli`; cachetools has no case with a sealed batch.
- **A `repr` forged for every input passes the held-out examples as well** (#219): a `$repr` is a
  text, and the hold-out only catches a forgery that is limited to what is visible.
- **The held-out examples of G2 are inputs of the tests that the fix adds**, public in the
  repository of the project, and one is in `witnesses.toml` in the name of a parametrized test; for
  G2 the run with the key shows that dokime catches a patch that fits what is visible, not that what
  is held out cannot be found out.
- **A first step cannot use an alternative constructor**, a class method such as `Version.parse`
  (#230); G2 builds its version with the class and keyword arguments.
- **The base of G4 fails because of the limit of Python on converting integers of more than 4,300
  digits**, which `PYTHONINTMAXSTRDIGITS` in the image could change.
- **The test with an identity made for it shows only the pass of a good case;** a bad case that
  fails at `sealed-examples` through the same path is missing, with the patch that special-cases the
  visible inputs of B1.
- **The audit of each case keeps its own storage of podman**, since the test points
  `XDG_DATA_HOME` to an empty directory so that no identity is found by default; that is what filled
  `/tmp` in the run with the key, and it may build the image of each case again in CI, which is not
  measured.
- **Part f took 360 and 356 seconds** in its last two runs, close to the 6 minutes of ADR-0078.
- **Overfitting by excluding the visible input has no case of its own**, of those that the review of
  the corpus left for B3; the others have one.
- **No case of B3d has a relation:** only `idempotent` at `cli` is measured, in one case of B2;
  `order-insensitive` and the relations at `function` still have no case.

**B3e closed on 2026-11-24.** `bench` computes the metrics of the corpus from the files of results
that its runs write ([ADR-0081](adr/0081-bench-computes-the-metrics-from-the-results-that-the-corpus-writes.md),
which amends ADR-0030; #233 to #237). On the push to `main` of `fd16c21`, run twice, it gives no
false accept and no false reject on the 32 cases, every case alike in both runs, and the
hold-out turns the 8 false accepts of the cases that only it catches into 0
(`tests/corpus/runs/fd16c21/`).

- [x] **The results of a run:** the test of the cases writes one line of JSON for each case, with
  the commit of the run (CORPUS-098, #234); each part of CI leaves its file, the parts check
  demands one line for each audit, all of one commit, and the job `corpus` keeps them as the
  artifact `corpus-results`, also when a part fails (#235); a file of a pull request records the
  merge commit that GitHub makes, so the figures come from a push to `main` (#236).
- [x] **`bench`:** BENCH-001 to BENCH-018 (#237). A case is accepted on `PASS` and rejected on
  `FAIL`; `ASK` is a question and `ERROR` is counted apart; each count says whether its run had
  the key and carries its Wilson interval of 95 %, which [Brown, Cai and DasGupta](https://projecteuclid.org/euclid.ss/1009213286)
  advise for n of 40 or less.
- [x] **The figures,** of the run 45451573331 on `fd16c21`, without the key:

  | | Every case | Without the case of W30 |
  |---|---|---|
  | False rejects | 0 of 10 (0 to 0.28) | 0 of 9 (0 to 0.30) |
  | False accepts, `fails-a-visible-example` | 0 of 8 (0 to 0.32) | the same |
  | False accepts, `edits-tests` | 0 of 3 (0 to 0.56) | the same |
  | False accepts, `breaks-existing-tests` | 0 of 2 (0 to 0.66) | the same |
  | False accepts, `breaks-a-relation` | 0 of 1 (0 to 0.79) | the same |
  | False accepts, `fails-a-held-out-example` | 8 of 8 (0.68 to 1), by design | the same |
  | Questions, errors | 0 of 32 each (0 to 0.11) | 0 of 31 each |

  The value of the hold-out: the 8 cases that only it catches are 8 false accepts without the key
  and 0 of 8 (0 to 0.32) with it, in the run of `held-out-run.toml`.
- [x] **Left out:** the rule of the row, a good case whose witness either blind reader labels not
  isolated or undecidable, computed from `tests/corpus/blind/` and `witnesses.toml`, leaves out only
  `nextver-bumps-build-only-versions`, of W30; a test checks it.
- [x] **Withdrawn, apart:** the five cases of G1, the good one a false reject caused by its
  contract, FAIL at `protected-paths`.
- [x] **Stability:** the two attempts of the run, the second started again from the web by the
  maintainer, gave the same verdict and first failing gate in the 32 cases, and the two files are
  the same byte for byte.

Its limits:

- **The intervals are wide:** with these n, 0 false accepts of 1 says only that the rate is below
  0.79, and of 8 that it is below 0.32; the counts show that nothing was missed on this corpus, not
  a rate.
- **The artifact of the first attempt, 14947688746, no longer exists:** the second attempt
  replaced it, and GitHub gives 404 for it. Its file was downloaded before the run was started
  again and is kept in `tests/corpus/runs/fd16c21/` with its sha256, which only this repository
  vouches for.
- **Stability rests on one pair of runs** of one commit, on the same runner image; a rerun does not
  change the code, so it measures only what varies without it.
- **The run with the key is read from `held-out-run.toml`**, made on an earlier commit of `main`
  that it does not record, and on the machine of the maintainer.
- **The minutes of a person per change**, a metric of ADR-0030, are not measured; the minutes of
  the review of each group of B3d are in `review.toml`, which is not the same thing.
- **The held-out examples of G2 are public** in the tests of its fix, as the note of B3d says.

### Block B · Closing note

**B4 closed on 2026-11-25, and block B with it**, with version 0.2.0 and the tag `v0.2.0`, which
the maintainer makes with its Release.

**The exit criterion of block B, no false accept on the four cheating techniques, holds on the
corpus, read literally**: in the run with the key of `held-out-run.toml` for the cases that only the
hold-out catches, and in the run of `fd16c21` for the rest (B3e). No case has a field for its
technique, so each bad case is given one by what its patch does, read from the `intent` of its
`case.toml`:

| Technique ([ADR-0030](adr/0030-the-harness-is-measured-on-a-corpus-with-known-verdicts.md)) | Cases | Caught by | False accepts |
|---|---|---|---|
| Editing tests | 3 | `protected-paths` | 0 of 3 (0 to 0.56) |
| Special cases | 10 | 3 a visible example, 7 only the hold-out | 0 of 10 (0 to 0.28); 7 of 7 without the key |
| Overloaded comparison | 2 | 1 a visible example, 1 only the hold-out | 0 of 2 (0 to 0.66); 1 of 2 without the key |
| State between calls | 1 | a visible example | 0 of 1 (0 to 0.79) |

- **Editing tests:** `skips-the-html-check-and-edits-its-test`, `nextver-changes-the-tests-to-fit`
  and `changes-the-default-token-and-the-tests` change a test of the pack so that the patch passes
  it, which the contract does not allow.
- **Special cases:** ten patches whose logic answers right only for the inputs that were seen, or
  for a narrower set than the requirement. Three are caught by a visible example, since the visible
  examples hold an input outside the special case: `fixes-only-a-code-block-before-the-blank`,
  `nextver-fixes-only-patch` and `replace-fixes-only-major`. Seven are caught only by the hold-out,
  since their condition is exactly the visible inputs, a property of them, or a table of their
  expected values: `strips-the-space-only-at-the-visible-tags`,
  `special-cases-the-visible-malformed-collections`, `special-cases-the-visible-tokens`,
  `orders-by-value-only-the-visible-identifiers`, `orders-by-value-only-the-visible-lengths`,
  `re-raises-only-for-the-visible-kinds-of-value` and `returns-the-visible-results`.
- **Overloaded comparison:** two patches that do not fix the logic but return an object that
  deceives what the judge compares. `answers-equal-to-a-malformed-collection` returns an object whose
  `__eq__` always holds, which deceives a comparison by `==`; a visible example catches it, since
  dokime compares the JSON or the `repr` outside the zone, never the object.
  `forges-the-repr-for-the-visible-malformed-collections` returns an object whose `__repr__` gives
  the text that `$repr` compares. It is counted here and not among the special cases because what it
  forges is what the comparison reads, as the maintainer asked in the review; it forges it only for
  the visible inputs, so only the hold-out catches it, and a forgery for every input would pass the
  hold-out as well (#219).
- **State between calls:** `keeps-the-first-next-prerelease` keeps the first result and gives it
  again on the calls after it, which a later step of the same example sees. State between examples
  has no channel left, since [ADR-0080](adr/0080-each-example-is-observed-in-a-container-of-its-own.md)
  observes each example in a container of its own.
- **Not one of the four:** six bad cases, none a false accept either:
  `hides-the-error-of-an-invalid-version`, a concealment that touches no test;
  `fixes-equality-and-leaves-the-ordering` and `matches-the-family-without-refusing-a-token`, partial
  fixes; `fix-with-a-regression-in-loose-lists` and `replace-with-a-regression-in-bump-minor`, which
  break existing tests; and `formats-a-short-code-block-differently-twice`, which breaks a relation.

Its scope: two techniques have one or two cases, so their counts show that nothing was missed on
this corpus, not a rate; and every bad case was written by the session that builds, not by an agent
that tries to cheat.

**The value of the hold-out is measured** (B3e): the 8 cases that only it catches are 8 false
accepts without the key and 0 of 8 (0 to 0.32) with it.

**The hypothesis that holding out by case catches overfitted solutions holds on constructed
cases.** The patches that overfit were written after the draw by the session that builds, knowing
which examples were held out, so that each fits what is visible and misses what is not: the
hold-out catches them by construction. What it shows is that dokime catches a patch overfitted to
the visible examples; not that an agent that overfits on its own is caught, which block C tests
again with the patches of an agent. The held-out examples of G2 are, besides, public in the tests of
its fix.

**The sealed gate does not run in CI in block B**
([ADR-0082](adr/0082-the-sealed-gate-does-not-run-in-ci-in-block-b.md), which amends ADR-0073): the
gate runs the code of the change, and the container would be the only barrier between that code and
the key. The maintainer runs the sealed audit locally before merging a pull request that adds or
changes a case or a contract with a sealed batch, and at the close of a block; nothing of it is
posted to the pull request. The sealed audit of this close is the run with the key of
`held-out-run.toml`, made with the harness at `51d2ff2`; since then only `bench` and the README of
`contract` (`3a597bb`) changed under `src/dokime`, and the tests of the corpus changed how they are
run, not what dokime audits, so it is not repeated. Part c of the job `corpus` was split again (#240), as ADR-0078 asks.

**What block B leaves open,** beyond the limits of each milestone above:

- **The hold-out against the patches of an agent**, in block C, where an agent writes the change.
- **The sealed gate without a person**, decided again before block C relies on it.
- **One recipient for the batches of the corpus**, though ADR-0073 asks for two; the batches sealed
  from now on carry the second.
- **The relations**: only `idempotent` at `cli` is measured, in one case.
- **The minutes of a person per change**, a metric of ADR-0030, not measured.

**For the strategic review of the maintainer**, which lives outside the repository, at the close of
block B:

- Whether the hold-out stays a gate of every change, given that it is measured only on constructed
  cases; the table of hypotheses says it becomes optional if it fails.
- How the sealed gate runs when nobody is there to type a passphrase, in block C.
- The second recipient of the sealed batches, and where the copy of the identity is kept.
- The review of the work done and of the plan left, before block C opens.

### Still to decide

Still to decide before a milestone opens. They are written down here and not decided in the
milestone that finds them:

- **After version 0.2 is published and before block C opens:** a review with the maintainer of
  the work done and of the plan left, which includes how to extend dokime to other languages, the
  probe of Java at the boundary `cli` among them; its scope is decided by the maintainer then. The
  parts of dokime that depend on Python are listed in the
  [architecture](architecture/README.md#what-depends-on-python).
- **For block D:** a case found in B0. The fix of mdformat `27e2ba3`, the good patch of a case of
  the corpus, passes every example and every test and widens the check `is_md_equal`, which then
  holds as equal documents that render differently: `*a* b` and `*a*b`, `a *b*` and `a*b*`,
  `[l](u) next` and `[l](u)next`. The fix that an agent wrote for the same examples does not, and
  the current mdformat keeps the wider rule. A change that passes everything and makes a part of
  the program worse is what block D looks for.
- **For block D:** `replace("1.2.3", major=1.5)`, which returns `1.2.3`, a candidate of
  unspecified behaviour, left out of B3 for the gate of the differences of behaviour.
- **Before C1:** what happens when two changes run at the same time on the same repository; and a
  limit of spending for a run, since the budgets of the flow count repetitions, not money; and the
  expected verdict of `replace-fixes-only-major` and `nextver-changes-the-tests-to-fit` under the
  loop of attempts, which may fix or clean them, so it depends on the budget of attempts.
- **Before the evidence reaches the agent, in block C:** each finding of the gate of the sealed
  examples carries in `lines` the line of its entry in `held_out`, which tells which held-out id
  failed; whether that reaches the agent is decided before the agent sees the evidence.
- **Before D2:** how the differences found outside the change are grouped without the gateway to
  a model.

The corpus runs as tests of the repository, which write the results of each case; `bench` computes
the metrics from them ([ADR-0081](adr/0081-bench-computes-the-metrics-from-the-results-that-the-corpus-writes.md)).

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

A ruleset on the tags of versions, `protect-version-tags` (Settings → Rules → Rulesets → New tag
ruleset), so that a published version keeps pointing at what was published:

- Target `v*`, active, with no one in the list of bypass.
- Updates, deletions and force pushes restricted; creations allowed, so that a version can be
  tagged.
