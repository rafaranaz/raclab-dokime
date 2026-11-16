# ADR-0059 · A mixed file protects the section that configures the tests

**Status:** accepted

## Context

[ADR-0056](0056-the-pack-names-the-configuration-of-its-tests.md) protects the configuration of the
tests through `tests.config`, and leaves open the files that hold the configuration of the tests
together with that of the project, such as `pyproject.toml` or `setup.cfg`: protecting the whole
file would refuse legitimate changes to the project. In the corpus, mdformat keeps its
configuration of pytest in `pyproject.toml`.
[ADR-0058](0058-existing-tests-runs-the-tests-of-the-base-on-the-code-of-the-patch.md) takes
`tests.config` from the base for `existing-tests`, and leaves these files open as well.

## Decision

- **The pack names each mixed file with the section that configures its tests**, such as
  `pyproject.toml` with `[tool.pytest.ini_options]`, `setup.cfg` with `[tool:pytest]` or `tox.ini`
  with `[pytest]`. The pack declares the section, so `packs` does not know pytest. The syntax is a
  requirement of `packs`.
- **A change to that section counts as a change of the tests for `protected-paths`.** The rest of
  the file stays free.
- **The pack puts in `tests.config` the files that pytest would read before the mixed file**, even
  when they do not exist, as ADR-0056 allows a pattern that matches no file. Otherwise a patch that
  adds a `pytest.ini` at the root would make the protected section void without touching it.
- **Authorising a mixed file in `may_modify_tests` authorises only its section.**
- **`existing-tests` does not restore that section.** If it changed, `protected-paths` already gives
  `FAIL` unless the contract authorises it. This is a declared limit: a mixed file is watched by one
  gate, not by two as ADR-0058 wants for the tests.

## Basis

Read in the commit of the corpus (`56b24ef`): the `pyproject.toml` of mdformat has
`[tool.pytest.ini_options]` with `addopts = "--strict-markers --strict-config"` and
`xfail_strict = true`. A patch that adds `--deselect` or `-p no:…` to `addopts` there changes which
tests run without touching a file of tests.

Measured on 2026-11-16 with pytest 8.3.4 in the image of the corpus, from the `configfile` that
pytest reports, with each pair of files in one directory: `pytest.ini` wins over all, even when it
is empty; then `.pytest.ini`; then `pyproject.toml`, only with `[tool.pytest.ini_options]`; then
`tox.ini`, only with `[pytest]`; then `setup.cfg`, only with `[tool:pytest]`. `pytest.toml` is not
read. When the command names a directory, as the pack of mdformat names `tests`, a `pytest.ini` in
that directory wins over the `pyproject.toml` of the root. For mdformat, then, a patch that adds an
empty `pytest.ini` at the root replaces `[tool.pytest.ini_options]` with no configuration at all,
dropping `--strict-markers`, `--strict-config` and `xfail_strict`; its pack puts `pytest.ini` and
`.pytest.ini` in `tests.config`, and the one in `tests/` is already under `tests.paths`. The list
depends on the version of pytest, as ADR-0056 says.

Read: the attacks documented on benchmarks of agents go through the configuration that pytest
loads ([BenchJack, section 3](https://arxiv.org/abs/2605.12673), on SWE-bench) and through the
process of the tests itself, by patching the report or calling `sys.exit(0)`
([a post on tianpan.co](https://tianpan.co/blog/2026-04-17-specification-gaming-production-ai-agents), April 2026, a secondary source). The second kind confirms the limit of
[ADR-0010](0010-threat-model.md): the tests run in the process of the code under check.

Looked for and not found: a tool that protects the configuration of pytest by section.

Reasoning, without a test: that a section changes for the tests far less often than the rest of a
mixed file, so protecting it refuses few legitimate changes.

## Alternatives considered

- **Protect the whole file.** It refuses legitimate changes to the project, such as its
  dependencies or its version.
- **Not protect it.** A patch could add `--deselect` or `-p no:…` to `addopts` and no gate would
  see it.
- **Protect the section and also run `existing-tests` with the section of the base**, through a
  `pytest.ini` generated from it and `-c`. Stronger, but it has to be shown that pytest behaves the
  same with the generated file, and it needs the section to be written into a tree.

## Consequences

- `protected-paths` reads the section of a mixed file in the base and in the patch and compares
  them, so it reads TOML and INI without knowing what the section means.
- `existing-tests` runs with the section of the patch, whether or not the contract authorised it;
  when it did not, `protected-paths` has already given `FAIL`.
- A mixed file has one gate where a test file has two.
- The packs of the corpus that have a mixed file gain its section when the field is built in A3.
