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
| A pack can be proposed from the CI configuration of a project | Milestone A2, with containers and access to registries | Packs are written by hand per project, declared as a cost of adoption |
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
| A3 Audit | A command that audits a change: baseline, protected paths, visible examples at the `cli` and `function` boundaries, existing tests, an aggregated verdict and an evidence file | `platform`, `verify`, `evidence`, `interfaces` | The exit criterion of the block, on the first ten cases of the corpus, labelled before they are run |
| A4 Audit in CI | A workflow that audits a pull request and attaches the evidence, enabled on this repository; version 0.1 | `interfaces` | A real pull request of this repository carries its evidence |

`interfaces` is opened three times in block A: in A1 for the command `contract check`, which only
reads the file, calls `contract` and shows its findings; in A2 for the command that builds an image
and checks a pack, which reads the pack and calls `packs`; and in A3 for `audit`. `platform` is
opened twice: in A2 for the adapter of the project repository
([ADR-0042](adr/0042-a-port-of-the-project-repository-composes-the-trees-that-are-built.md)), and
in A3 for the stores and the clock. The scopes of a module are
opened by increments, as `core` is
([ADR-0036](adr/0036-a-milestone-may-open-an-increment-of-a-later-module.md)).

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
- The four CI checks must pass (`lint, types and tests`, `governance checks`,
  `commits and branch scope`, `dependency audit`), on a branch that is up to date with `main`.
- Linear history required; force pushes and deletion blocked.
