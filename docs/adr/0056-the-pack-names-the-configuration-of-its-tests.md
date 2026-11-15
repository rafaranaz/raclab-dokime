# ADR-0056 · The pack names the configuration of its tests, which is protected

**Status:** accepted

## Context

[ADR-0016](0016-verification-in-a-container-on-base-plus-patch.md) makes protected paths of the
tests, **their configuration** and the directory of the harness: a change to them is dropped from
the patch unless the contract allows it. The pack names its tests with the field `tests.paths`,
in the table of fields of the [requirements of `packs`](../requirements/packs.md#table-of-fields).
Nothing names their configuration, so the gate `protected-paths` of A3 could not protect it. A
change to a `conftest.py` or to a file of configuration can skip or rewrite tests without touching
a file of tests.

## Decision

- **The pack gains a mandatory field, `tests.config`**: the patterns of the paths that configure
  how its tests run. They are protected like the tests. The field goes into the table of fields of
  the requirements of `packs` when A3 opens.
- **It is mandatory**, so that whoever writes a pack has to say what configures its tests.
- **A pattern may match no file today.** It protects a file that a patch would create, such as a
  `conftest.py` or a `pytest.ini` in a project that has neither.
- **What the field adds is what `tests.paths` does not already cover.** With `tests/**`, a
  `tests/conftest.py` is already protected; what is left is the configuration outside the
  directory of the tests, such as `.pytest.ini` at the root, or a `conftest.py` at the root or in
  `src/`.
- **What the field holds depends on the tool of the tests and its version**, which is why it lives
  in the pack and not in the policy. For pytest, the files it reads are listed in the basis.
- **Files that hold the configuration of the tests together with that of the project**, such as
  `pyproject.toml` or `setup.cfg`, are still open: protecting the whole file would refuse
  legitimate changes to the project. mdformat, in the corpus, keeps its configuration of pytest in
  `pyproject.toml`, so this has to be decided when A3 opens, with the cases of the corpus in front.

## Basis

Read in the documentation of pytest: pytest takes its configuration from the first of
`pytest.toml`, `.pytest.toml`, `pytest.ini`, `.pytest.ini`, `pyproject.toml` (with a table
`[tool.pytest.ini_options]`), `tox.ini` (with a section `[pytest]`) and `setup.cfg` (with a
section `[tool:pytest]`) found from the directory of the tests upwards
([pytest](https://docs.pytest.org/en/latest/customize.html)); and from `conftest.py` files, which
it collects in the directories of the tests and above them.

Measured on 2026-11-15:

- The list depends on the version. pytest 8.3.4, the one in the images of the corpus, reads
  `pytest.ini` and `.pytest.ini` and does not read `pytest.toml` or `.pytest.toml`; pytest 9.2
  reads them.
- In the corpus, cachetools has no configuration of pytest; python-semver has `.pytest.ini` and
  `tests/conftest.py`; mdformat has `[tool.pytest.ini_options]` in `pyproject.toml` and
  `tests/conftest.py`.

Reasoning, without a test: that a mandatory field makes the person think about the configuration
once, when the pack is written.

## Alternatives considered

- **Protect a fixed list of names in the harness.** It knows one tool, and one version of it, in
  code, which the module map forbids to `packs` ("Know languages in code. Everything is
  declarative").
- **Put the list in the policy.** The policy holds values of the harness; how a project runs its
  tests is what the pack describes.
- **Leave the field optional.** A pack without it would protect only its tests, and nobody would
  notice.

## Consequences

- Writing a pack takes one more decision, and the three packs of the corpus gain the field.
- The check of a pack refuses a pack without `tests.config`.
- A pack written for one version of pytest may have to change when the image moves to another.
- The open case of mixed files has to be decided before the gate `protected-paths` is built.
- How the self-check counts a commit that changes only configuration and code, when it chooses its
  candidates with `tests.paths`, is decided in A3.
