# ADR-0057 · The cases of the corpus come from witnesses past the second, that fit a boundary

**Status:** accepted, amended by [ADR-0061](0061-the-doctests-of-the-documents-are-tests-of-the-pack.md)

## Context

[ADR-0055](0055-a-case-of-the-corpus-is-labelled-by-how-it-is-built.md) takes the good patches of
the corpus from the witnesses that the self-check of a pack finds, and says that the self-check,
which stops at the second witness, gives two for each project, six in all, enough for the ten cases
of A3; looking past the second witness would be needed only in block B. On 2026-11-15 the six
witnesses were read one by one, and only one of them can be a case.

## Decision

This amends ADR-0055 in two points; the rest of it stands.

- **Looking for witnesses past the second is needed now, for A3.** It is done with a script that
  runs the order, the candidates and the rule of a witness of the harness (ADR-0044) over more
  candidates. The script enters the repository in the scope `corpus` when A3 opens, with its
  requirement, and its results as a fixture
  ([ADR-0050](0050-an-experiment-enters-the-repository-as-a-test.md)). The self-check of a pack is
  not changed: it still stops at the second witness.
- **A witness becomes a good patch only if it passes two filters**, besides being a witness:
  - *isolated*: its change of code is the fix, not a refactor nor a change of the tooling of the
    tests;
  - *expressible*: what it fixes can be written as examples at a boundary of the first version of
    the contract ([ADR-0039](0039-what-a-contract-of-the-first-version-may-say.md)): a function of
    a module called with values of JSON, or a command line.

  A witness that fails a filter is recorded with the reason, because the share that fails the
  second is a measure in itself.
- **The good patch is everything the commit changes outside the paths of the tests of the pack**,
  documentation included, and not only the code.
- **The ten cases of A3 come from three good patches**, one for each pair of project and boundary
  that the corpus allows: python-semver at `function`, python-semver at `cli` and mdformat at
  `cli`, with seven bad patches derived from them across the three labels of the exit criterion.

## Basis

Measured on 2026-11-15, running the order, the candidates and the rule of a witness of the harness
over the first 25 candidates of each project (mdformat stopped at 16, at the time limit of the
session that measured), with pytest 8.3.4 in a local environment instead of a container:

| Project | Candidates looked at | Witnesses |
|---|---|---|
| cachetools | 25 | 14 |
| python-semver | 25 | 18 |
| mdformat | 16 | 7 |

The test of this measurement comes with the script, in the scope `corpus`.

Read in the change of each of the six first witnesses: one is a refactor of 490 lines, one changes
the tooling of the tests, and three fix behaviour that a contract of the first version cannot reach
(an object with `__index__`, a class given as an argument, a plugin installed). Only python-semver
`0bd62d4` fits, through the function of the module `semver.replace`.

Run, for the three pairs: python-semver `0bd62d4` at `function`, python-semver `4e09ef0` at `cli`
with `python -m semver nextver`, and mdformat `27e2ba3` at `cli` with `python -m mdformat -`. For
each good patch, run against its base, the examples of change fail on the base and pass with the
fix, and no test that passed on the base stops passing (511, 354 and 4,267 tests). The seven bad
patches pass the examples or break tests exactly as their label says. With only the change under
`src/`, the good patch of `nextver` broke a doctest in `docs/` that the commit updated, and the
harness would have refused a good patch; that is why the good patch takes everything outside the
tests.

Read, not run: the share of witnesses that fit in each project. In python-semver most witnesses
reach a function of the module or the command `pysemver`; in cachetools almost all are decorators
and methods of classes, which a function called with values of JSON cannot reach; in mdformat at
least two reach the command `mdformat`.

Reasoning, without a test: that the share of real fixes that fit a boundary depends on the style of
a library more than on the library being small.

## Alternatives considered

- **Extend the boundary `function` to build objects and call methods.** It would let cachetools in,
  and it changes the format of the contract and ADR-0039. It is decided when the share of fixes that
  do not fit, measured across the corpus, says it is needed; not to reach the ten cases of A3.
- **Let the self-check go past the second witness.** It would make every self-check slower to find
  cases for the corpus, which is a different job.
- **Pick the cases by hand from the history.** It brings back the choice that taking them from the
  witnesses was meant to remove.
- **Take as the good patch only the change of code.** A commit that updates its documentation with
  the fix would give a good patch that breaks a doctest.

## Consequences

- The hypothesis that most real requirements fit as examples at a boundary, confirmed in A0 on
  changes chosen by hand, is measured again on changes taken from the history; the published
  results give both numbers.
- cachetools gives no case to A3. Its pack still runs in the job `corpus`.
- The script that finds the witnesses is maintained with the cases, and its results are recorded so
  that the choice can be repeated.
- The note of the close of block A in the roadmap gives the share of fixes that do not fit.
