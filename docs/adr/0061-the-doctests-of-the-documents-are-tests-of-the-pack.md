# ADR-0061 · The doctests of the documents are tests of the pack, and those of the docstrings are a declared limit

**Status:** accepted

## Context

pytest can run the examples of a document or of a docstring as tests. python-semver does so, and its
pack counts as tests only `tests/**`. A patch that edits a doctest of a document to make it fit
would not be seen as one that edits tests, and
[ADR-0058](0058-existing-tests-runs-the-tests-of-the-base-on-the-code-of-the-patch.md) would not
take it from the base.
[ADR-0057](0057-the-cases-of-the-corpus-come-from-witnesses-that-fit-a-boundary.md) takes as the
good patch everything the commit changes outside the tests of the pack, documentation included.

## Decision

This amends ADR-0057 in what the good patch is; the rest of it stands.

- **The documents whose examples pytest runs are tests**, and go into `tests.paths` of their pack.
  For python-semver that is `docs/**/*.rst`, which also takes the files at the root of `docs/`:
  pytest collects them too.
- **A fix that changes the behaviour a doctest documents has to update it**, and the contract
  authorises that file in `may_modify_tests`. With ADR-0058 the doctest of the base runs, and it
  expects the old behaviour, so without that authorisation a good patch would give `FAIL`.
- **The good patch is everything the commit changes outside the paths of the tests of the pack,
  plus the files that its contract authorises in `may_modify_tests`.** The case
  `python-semver/nextver-bumps-build-only-versions` authorises
  `docs/usage/increase-parts-of-a-version_prereleases.rst`.
- **The doctests of docstrings are a declared limit.** When a project has its code in `testpaths`,
  or a pack names `src/` in its command, `--doctest-modules` makes tests of the docstrings of the
  code: tests inside files of code, which cannot be protected by path without protecting the code,
  nor restored without undoing the fix. A patch that edits the example of a docstring to make it
  fit is seen by no gate of block A. How the pack and the evidence mark it is decided when the gate
  is built.

## Basis

Read in python-semver, at `b6e83e3`, `a8bb4f89` and `15a42d0`: `.pytest.ini` has
`testpaths = tests docs`, `--doctest-glob='*.rst'` and `--doctest-modules`. The command of its pack
names no path, so pytest uses `testpaths`, and the doctests of `docs/` already run in its
self-check.

Measured on 2026-11-16 in the image of the corpus, at `b6e83e3`: pytest collects 534 tests, and the
21 outside `tests/` are all `docs/**/*.rst`. None comes from `src/`, because `--doctest-modules`
only goes through what is under `testpaths`. So python-semver does not have the limit of the
docstrings; it is stated for the projects that would.

Measured the same day, the self-check of python-semver with `docs/**/*.rst` in `tests.paths`
passes in 22 s. Its first witness is `b6e83e3`, "Bump version 3.1.0 -> 3.1.1": its test is
`docs/usage/semver-version.rst`, whose `>>> semver.__version__` goes from `'3.1.0'` to `'3.1.1'`.
For the self-check it is not false: it shows that the command runs tests and that a red that turns
green is seen, which is what the self-check has to prove. As a fix it is, and for the cases of the
corpus that is what the filter *isolated* of ADR-0057 removes.

Measured on 2026-11-16 by the session that built the cases, with pytest 8.3.4 locally and not in
the container, over the first 25 candidates of python-semver with `docs/**/*.rst` in `tests.paths`:
21 witnesses, against 18 among its first 25 candidates with `tests/**` alone. Of the 21:

- 5 are version bumps or changes of configuration whose only test that turns green is
  `docs/usage/semver-version.rst`: `b6e83e3`, `9c19156`, `bae0b7c`, `cc4ae07` and `6208a54`;
- 1 is a fix that was not seen before, because its only test is a doctest: `fdec4ae`,
  "fix(next_version): reset prerelease when token changes";
- the commits of the cases, `0bd62d4` and `4e09ef0`, are still witnesses with the same tests, so
  the cases do not change.

## Alternatives considered

- **Leave the documents out of `tests.paths`.** A patch that edits a doctest to make it fit would
  not be seen as one that edits tests, and `existing-tests` would run the edited doctest.
- **Keep the good patch as everything outside the tests.** The good patch of `nextver` would not
  carry the doctest it updates, and with the doctest of the base it would give `FAIL`.
- **Protect the files of code that have doctests.** Every fix would touch a protected path.

## Consequences

- The candidates of python-semver change with `docs/**/*.rst` in `tests.paths`; the search for
  witnesses of ADR-0057 was repeated for that project, and its result is in the basis.
- A release that updates a version shown in a doctest is a witness of the self-check; it never
  becomes a good patch, because it is not isolated.
- The pack of python-semver changes in a pull request of the scope `corpus`, after this one.
- The limit of the docstrings is written down before any project of the corpus has it.
