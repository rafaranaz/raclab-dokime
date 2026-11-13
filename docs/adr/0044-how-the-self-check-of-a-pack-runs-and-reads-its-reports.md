# ADR-0044 · How the self-check of a pack runs and reads its reports

**Status:** proposed

## Context

[ADR-0041](0041-the-environment-of-a-verified-project-is-a-dockerfile.md) says what the self-check
of a pack proves: among the latest commits that change a test and code that is not a test, at
least two of the first ten have a test that fails on the parent and passes on the commit.
[ADR-0042](0042-a-port-of-the-project-repository-composes-the-trees-that-are-built.md) gives the
port that composes the trees, and
[ADR-0043](0043-tests-run-only-on-an-engine-that-enforces-the-limits.md) the engines that run
them. Still open: which module drives the loop, what "the latest commits" means, and how a report
in JUnit XML is read when the code that wrote it is not trusted. In milestone A3 that code is the
change of an agent.

## Decision

### Who runs it

- **`packs` drives the self-check.** It chooses the candidates, asks the port of the project
  repository for each tree, runs the tests on both sides and applies the rule of witnesses. It
  receives the ports from `interfaces`.
- **One reusable operation.** The loop is built on one operation of `packs`: run the tests of a
  pack on a directory and give the outcome of each test. `verify` uses the same operation in
  milestone A3.

### The order of the candidates

- **The port gives the history, and `packs` orders it.** The port of the project repository gives
  the history from a commit: every commit reachable from it, with its commit date and its parents
  in the order the commit names them. This amends ADR-0042, where the port lists commits.
- **The rule of order is ours.**
  - No commit is placed before a commit that descends from it.
  - Among the commits that can come next, the one with the later commit date goes first.
  - On equal dates, the one that could come next earlier goes first. The parents of a commit
    become able to come next in the order the commit names them.
  - A commit that does not have exactly one parent is left out, on purpose. That removes the
    merges and the first commits, and a candidate needs one parent.
- **What an adapter of the repository must do.** It ignores replace objects (`git replace`) and
  refuses a shallow clone.

### What counts

- **A witness is a test that goes from red to green.** It is not a commit that fixes a defect.
  Refactors and removed features count, because the rule measures what the pack needs: that the
  environment shows a test change state.
- **Candidates that cannot be witnesses stay candidates.** That covers a commit that changes only
  tests and documentation, and one whose tests were only adapted (mdformat `10307b9`). The pack
  has no field to exclude them.
- **The numbers stay: two witnesses among the first ten candidates.**

### How a report is read

- **The adapter of the verification runtime reads the report.** It reads it after the run and
  gives `packs` the outcome of each test. The domain receives values and does no input or output.
- **Limits and codes.** Each failure is a finding with the verdict `ERROR`:

  | Case | Code |
  |---|---|
  | The report is larger than 32 MiB. At most the limit plus one byte is read. The pack cannot raise the limit. | `report-too-large` |
  | The path holds a symbolic link at any of its parts, or the report is not a regular file. The path is opened part by part from the output directory, each part with `O_NOFOLLOW`. | `report-not-a-file` |
  | The report has a `DOCTYPE`. It is refused with handlers of `pyexpat`, before any entity is declared. | `report-has-doctype` |
  | The report is not well-formed XML. | `report-unreadable` |
  | The process that reads the report dies or reaches a limit. | `report-reader-failed` |
  | The Expat of the Python that runs the harness is older than 2.8.5. This is checked when the adapter starts. | `expat-too-old` |

- **The report is read in a process of its own.** That process has `RLIMIT_AS` at 512 MiB and
  `RLIMIT_CPU` at 10 seconds. The adapter opens the file and passes the open descriptor, so the
  process never resolves the path. This bounds memory and processor time, and it turns a crash of
  the parser into `ERROR`. **It is not isolation.** The process runs with the permissions of the
  person. If a defect of Expat allowed code to run, that code could do what the person can do.
- **The version of Expat is recorded.** The value of `pyexpat.EXPAT_VERSION` goes into the
  evidence.
- **A report that cannot be read makes the self-check `ERROR`.** The candidate is not dropped in
  silence, so that a pack is never judged on fewer candidates than the rule says.

## Basis

Verified on 2026-11-12 and 2026-11-13, on local clones of the corpus (cachetools `1ce79ef`,
python-semver `b6e83e3`, mdformat `56b24ef`), the originals untouched.

- **Self-check.**
  - cachetools gave 7 witnesses among the first 10 candidates, python-semver 8 and mdformat 4.
  - A pack of cachetools that installs the released version from PyPI instead of the code under
    test gave 0 of 10.
  - Among the witnesses there are refactors and removed features.
  - Two candidates cannot be witnesses for the reasons above: cachetools `6a89b7c` and
    python-semver `f3c7138` change only tests and documentation, and mdformat `10307b9` only
    adapts its tests to a new fixture.
- **Order.**
  - Read in the manual of `git rev-list`:
    - the default order is "reverse chronological";
    - `--date-order` shows no parent before all its children, and otherwise follows the commit
      timestamp;
    - `--topo-order` gives two valid outputs for the example of the manual itself;
    - nothing is said about equal dates.
  - Tested in repositories made for the test:
    - with a child older than its parent, the default order showed the parent first, and
      `--date-order` did not;
    - equal dates were broken by the order of the parents in the merge;
    - the output was identical with git 2.32.0, 2.40.1, 2.47.3 and 2.54.0, with and without a
      commit graph, and in a fresh clone;
    - a `git replace --graft` changed a list of 7 commits to 1, and `--no-replace-objects`
      restored it;
    - a clone with `--depth 3` gave 3 commits instead of 6.
  - The rule above, written in 25 lines of Python over `git log --format='%H %ct %P'`, gave
    exactly the output of `git rev-list --date-order --no-merges`, ties included, once roots were
    removed. It was compared on six repositories: two made for the test, the three of the corpus,
    and the repository of git itself (82,925 commits, 61,446 listed).
  - On git, reading the history took 3.4 s and ordering it 0.65 s, with 75 MB of memory.
- **Report.**
  - The largest of the 125 reports of the self-checks is 462 KB, mdformat with 4,286 tests.
    None has a `DOCTYPE`.
  - A reader built on `pyexpat` with `StartDoctypeDeclHandler` and `EntityDeclHandler` that
    raise refused the billion laughs, the quadratic blowup, two external entities, an external DTD
    and a request to a local server. Each was refused in under 0.01 s with about 11 MB.
  - The report of mdformat was read in 0.02 s with 14 MB.
  - A single attribute of 30 MB, under the limit, used 141 MB.
  - The C parser of ElementTree does not expose those handlers, so `pyexpat` is used directly.
  - Opening the path part by part with `O_NOFOLLOW` and `dir_fd`, and checking with `fstat` for
    a regular file, refused:
    - a link in an intermediate directory pointing outside the output directory;
    - a link in an intermediate directory pointing inside it;
    - a link as the final file;
    - a FIFO.

    It read the normal report.
- **Process of its own**, with `RLIMIT_AS` and `RLIMIT_CPU` set before the reader starts:

  | Case | Result |
  |---|---|
  | The report of mdformat | 4,286 tests, 0.22 s |
  | A 30 MB attribute under 512 MiB | read |
  | The same under 64 MiB | "out of memory", exit 1 |
  | A forced segmentation fault | the process ended on `SIGSEGV` |
  | A loop under a limit of 1 s | the process ended on `SIGKILL` after 1.24 s |

  Each child process costs about 0.075 s to start, about 3 s for the 40 reports of a
  self-check.
- **Expat, read in its `Changes` file.** Several fixed defects need no DTD:

  | Version | CVE | What it fixed |
  |---|---|---|
  | 2.4.5 | CVE-2022-25235 | malformed UTF-8 in names, with known exploits |
  | 2.8.1 | CVE-2026-45186 | quadratic time on attribute names |
  | 2.8.4 | CVE-2026-66046, CVE-2026-76641 | quadratic time on attribute lookups (not checked whether they need a DTD) |
  | 2.8.5 | CVE-2026-93990 | malformed UTF-16, which a document only has to declare |
  | 2.10.0, of 2026-11-02 | CVE-2026-118370 | an overflow in `storeAtts` |

  The Python here has Expat 2.9.0, so it lacks the last fix. The file opens by saying that
  Expat has unfixed security issues, listed in its issue 1160 without details. Requiring 2.10.0
  would refuse every Python available here.
- **defusedxml**, read on PyPI and in its source:
  - it has `forbid_dtd`, off by default, set through the same three handlers of `pyexpat`;
  - it loads the pure Python module of ElementTree with a variant of `import_fresh_module`;
  - it does not bound the size and does not check the version of Expat;
  - its last stable release is 0.7.1, of 2021; 0.8.0rc2, of 2023, never became final; its last
    commit is of October 2023.

Not checked: macOS and Windows; whether `RLIMIT_AS` is enforced on macOS; reports of tools other
than pytest. Reasoning, without a test: that a pack never needs a larger report in the first
version (32 MiB holds about 300,000 tests at the size measured); the limits of 512 MiB and 10 s
for the reader.

## Alternatives considered

- **A new domain service drives the self-check.** It would duplicate in another module the rule
  that `packs` holds. `verify`, the other candidate, does not exist in A2.
- **The order given by `git rev-list`, required of the git adapter only.** A second adapter would
  have nothing to match. Ties depend on a behaviour of git that its manual does not state.
- **`--topo-order` or the order by author date.** The manual of the first allows two outputs.
  The author date is set by whoever writes the commit and is not the date of the history.
- **The order in `core`.** Only the self-check needs it; the audit of A3 does not.
- **A field of the pack to exclude candidates**, such as paths that do not count as code. All
  three packs pass without it.
- **defusedxml with `forbid_dtd=True`.** It works the same way and adds a dependency without a
  stable release since 2021 that relies on reloading a module of the standard library. It gives
  neither the limit of size nor the check of version.
- **No version check, since the `DOCTYPE` is refused.** Several fixed defects of Expat need no
  DTD.
- **Read the report in the process of the harness.** A crash of the parser would end the harness,
  and memory would be bounded only by the size of the file.
- **Read the report inside the container that ran the tests.** That would truly isolate the
  reader. The image is the one of the project, and the harness would have to trust a reader that
  runs inside it, written by the same code it checks.
- **A field of the pack to raise the limit of the report.** No pack of the corpus comes near the
  limit.

## Consequences

- The self-check gives the same first ten candidates on every machine and with every adapter.
- Ordering loads the whole history. That was measured up to 82,925 commits, not beyond.
- A shallow clone cannot be self-checked. Neither can a repository where the history differs
  only through replace objects.
- `verify` in A3 reads reports with the same operation, and therefore with the same limits.
- A report that the harness cannot read never passes. It ends in `ERROR`, and a person looks at
  it.
- On Windows there is no `dir_fd`, so the safe opening of the report does not work there: known
  limit.
- A harness on a Python whose Expat is older than 2.8.5 refuses to read reports. The minimum has
  to be reviewed when Expat publishes fixes.
- The process that reads the report bounds resources. It does not contain a defect of Expat that
  allows code to run.
- ADR-0042 is amended: the port gives the history instead of listing commits.
- The module map changes with this decision. The port of the verification runtime reads the
  report and gives the outcome of each test. The port of the project repository gives the
  history.
