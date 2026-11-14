# ADR-0045 · A test report is read by a bounded reader that refuses any DTD

**Status:** accepted

## Context

[ADR-0041](0041-the-environment-of-a-verified-project-is-a-dockerfile.md) makes the pack name a
report in JUnit XML that the test command writes in the output directory. The code that writes it
is the code under test, and in milestone A3 the change of an agent: it can write a report of any
size, put a link where the report should be, or declare entities that expand without end. The
self-check of a pack reads those reports now, and `verify` reads them in A3.

## Decision

### Who reads it

- **The adapter of the verification runtime reads the report.** It reads it after the run and
  gives the outcome of each test to the module that called the port. The domain receives values
  and does no input or output.
- **The outcome of a test is a type of `core`.** `Outcome` and `Report`, today in
  `src/dokime/packs/selfcheck.py`, move to `core`, because the port returns them and an adapter
  imports only `core`.
- **The limits are policy, and the adapter receives them.** `core` defines the limits of reading a
  report as one value, next to `Outcome` and `Report`, with the three limits below. The module that
  calls the port (`packs`, and `verify` in A3) passes that value in each call. In the first version
  neither the pack nor an option of the command changes it.

### Limits and codes

Each failure is a finding with the verdict `ERROR`. The module that called the port adds it to its
result.

| Case | Code |
|---|---|
| The report is larger than 32 MiB. At most the limit plus one byte is read. The pack cannot raise the limit. | `report-too-large` |
| The path holds a symbolic link at any of its parts, or the report is not a regular file. The path is opened part by part from the output directory, each part with `O_NOFOLLOW`. | `report-not-a-file` |
| The report has a `DOCTYPE`. It is refused with handlers of `pyexpat`, before any entity is declared. | `report-has-doctype` |
| The report is not well-formed XML. | `report-unreadable` |
| The process that reads the report dies or reaches a limit. | `report-reader-failed` |
| The Expat of the Python that runs the harness is older than 2.8.5. This is checked when the adapter starts. | `expat-too-old` |

### A process of its own

- **The report is read in a process of its own.** That process has `RLIMIT_AS` at 512 MiB and
  `RLIMIT_CPU` at 10 seconds. The adapter opens the file and passes the open descriptor, so the
  process never resolves the path.
- **This bounds memory and processor time, and it turns a crash of the parser into `ERROR`. It is
  not isolation.** The process runs with the permissions of the person. If a defect of Expat
  allowed code to run, that code could do what the person can do.
- **The version of Expat is recorded.** The value of `pyexpat.EXPAT_VERSION` goes into the
  evidence.
- **The minimum of Expat lives in the adapter, not in `core`.** It is one constant of the adapter
  that reads reports, next to the check made when the adapter starts. It is not policy: it says
  which versions of the parser this adapter uses are known to be unsafe, so a caller has no reason
  to ask for another, and an adapter with another parser would have another minimum. Raising it is
  a change of `sandbox` alone, whose commit quotes the entry of the `Changes` file of Expat that
  justifies it. Since the evidence records the version found, a run can be judged later against a
  newer minimum.

## Basis

Verified on 2026-11-12 and 2026-11-13 with Python 3.13 and Expat 2.9.0, on the reports of the
self-checks of the corpus (cachetools, python-semver, mdformat).

- **Reports.**
  - The largest of the 125 reports of the self-checks is 462 KB, mdformat with 4,286 tests.
    None has a `DOCTYPE`.
  - A reader built on `pyexpat` with `StartDoctypeDeclHandler` and `EntityDeclHandler` that
    raise refused the billion laughs, the quadratic blowup, two external entities, an external DTD
    and a request to a local server. Each was refused in under 0.01 s with about 11 MB.
  - The report of mdformat was read in 0.02 s with 14 MB.
  - A single attribute of 30 MB, under the limit, used 141 MB.
  - The C parser of ElementTree does not expose those handlers, so `pyexpat` is used directly.
- **Path.** Opening the path part by part with `O_NOFOLLOW` and `dir_fd`, and checking with
  `fstat` for a regular file, refused:
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
- **Imports.** The contract "Adapters import only core" of `lint-imports` keeps `sandbox` from
  importing `packs`, where `Outcome` lives today.

Not checked: macOS and Windows; whether `RLIMIT_AS` is enforced on macOS; reports of tools other
than pytest. Reasoning, without a test: that a pack never needs a larger report in the first
version (32 MiB holds about 300,000 tests at the size measured); the limits of 512 MiB and 10 s
for the reader; that the caller, and not the adapter or the composition root, is the right place
to give the limits, and that the adapter is the right place for the minimum of Expat.

## Alternatives considered

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
- **The adapter returns the bytes and `packs` parses them.** The domain would start a process to
  bound the parser, which is input and output.
- **The limits as constants of the adapter.** The module map says that `sandbox` does not decide
  policy, it receives it.
- **The limits given by `interfaces` when it builds the adapter.** The composition root would hold
  a value of policy, and `verify` could not ask for other limits than the self-check.
- **The minimum of Expat in `core`, with the limits.** `core` would name a library that only one
  adapter uses, and a caller could lower a floor of safety.
- **The minimum of Expat as a constraint of the project**, in `pyproject.toml`. Expat comes with
  the build of Python, often linked to the library of the system, not with a package, so no
  constraint on dependencies can require it.
- **A field of the pack to raise the limit of the report.** The code under check would choose its
  own limit, and no pack of the corpus comes near it.

## Consequences

- `verify` in A3 reads reports with the same adapter, and therefore with the same limits unless it
  passes others.
- A report that the harness cannot read never passes. It ends in `ERROR`, and a person looks at
  it.
- On Windows there is no `dir_fd`, so the safe opening of the report does not work there: known
  limit.
- A harness on a Python whose Expat is older than 2.8.5 refuses to read reports. The minimum is
  reviewed on its own, in `sandbox`, when Expat publishes fixes.
- The process that reads the report bounds resources. It does not contain a defect of Expat that
  allows code to run.
- `Outcome` and `Report` move in two branches, one per scope: `core` adds them, and then `packs`
  imports them from `core` and drops its own.
- The row of the verification runtime in the module map changes: it also reads the report and
  gives the outcome of each test.
