# ADR-0059 · A mixed file protects the section that configures the tests

**Status:** proposed

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
- **Authorising a mixed file in `may_modify_tests` authorises only its section.**
- **`existing-tests` does not restore that section.** If it changed, `protected-paths` already gives
  `FAIL` unless the contract authorises it. This is a declared limit: a mixed file is watched by one
  gate, not by two as ADR-0058 wants for the tests.

## Basis

Read in the commit of the corpus (`56b24ef`): the `pyproject.toml` of mdformat has
`[tool.pytest.ini_options]` with `addopts = "--strict-markers --strict-config"` and
`xfail_strict = true`. A patch that adds `--deselect` or `-p no:…` to `addopts` there changes which
tests run without touching a file of tests.

Read: the attacks documented on SWE-bench go through the configuration that pytest loads
([BenchJack, section 3](https://arxiv.org/abs/2605.12673)) and through the process of the tests
itself, by patching the report or calling `sys.exit(0)` (a post on tianpan.co, April 2026, a
secondary source). The second kind confirms the limit of
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
