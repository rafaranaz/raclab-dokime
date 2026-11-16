# ADR-0058 · existing-tests runs the tests of the base on the code of the patch

**Status:** accepted

## Context

The gate `existing-tests` fails when a test that passed in the baseline fails or disappears
([ADR-0017](0017-damage-outside-the-change-against-a-baseline.md)). Nothing says which version of
the tests it runs when a patch edits them: the version of the patch, the version of the base, or
both. When the agent works under the harness, `protected-paths` restores the protected files
([ADR-0016](0016-verification-in-a-container-on-base-plus-patch.md)), so the tests of the base
run; for a change that arrives already made, the question is open. The review of the ten cases of
the corpus left it open for A3, before `existing-tests` is built.

## Decision

- **`existing-tests` runs the tests of the base on the code of the patch.** The tree it runs is the
  base with the patch applied, with the paths of `tests.paths` and of `tests.config`
  ([ADR-0056](0056-the-pack-names-the-configuration-of-its-tests.md)) taken from the base. A file
  that the patch adds under those paths is not in that tree.
- **Except the files that the contract authorises in `may_modify_tests`**, which run in their
  version of the patch, so that the authorisation keeps its meaning.
- **A test of an authorised file that disappears gives `ASK`**, and the evidence lists it. Removing
  it can be legitimate, when a file is renamed or the tests are reorganised, or a trick, when the
  file is emptied, and the two cannot be told apart mechanically.
- **`visible-examples` runs on the same tree as `existing-tests`**: the code of the patch, with
  `tests.paths` and `tests.config` from the base, except what is authorised. The examples call the
  code at its boundary and do not load the tests, so the environment is built once. What the patch
  changes in the tests is looked at only by `protected-paths`.
- The files that mix the configuration of the tests with that of the project stay open, as
  ADR-0056 says.

## Basis

Read in the code of SWE-bench v3.0.0 (`swebench/harness/test_spec/python.py`): the evaluation
runs `git checkout <base_commit>` on the files that the reference test patch modifies, before
applying that patch and again at the end, so it runs the tests of the base, plus the reference
ones, on the code of the model. It restores only those files. BenchJack showed that a
`conftest.py` at the root, created by the agent, survives that restoration and rewrites the
outcome of the tests ([Wang et al., section 3](https://arxiv.org/abs/2605.12673)); taking
`tests.paths` and `tests.config` from the base closes that hole here. Agents edit tests even when
told not to ([ImpossibleBench](https://arxiv.org/abs/2510.20270),
[EvilGenie](https://arxiv.org/abs/2511.21654)).

Measured while the cases were built, in the session that drafted and reviewed them, running the
cases with the scripts of the draft of the corpus, by hand, with pytest 8.3.4 in a local environment
and not in the container, on 2026-11-15 and 2026-11-16, on the two cases labelled *edits tests*:

| Case | With the tests of the patch | With the tests of the base |
|---|---|---|
| `python-semver/nextver-changes-the-tests-to-fit` | 0 of 354 fail | 3 fail (`tests.test_bump::test_should_versioninfo_bump_*`) |
| `mdformat/skips-the-html-check-and-edits-its-test` | 0 of 4,267 fail | `tests.test_plugins::test_ast_changing_plugin` fails |

With the tests of the patch only `protected-paths` would catch them; with those of the base,
`existing-tests` catches them too. The test of this measurement comes with the scope `corpus`.

Looked for and not found: a tool that runs both versions of the tests and warns when they differ.

Reasoning, without a test: that in the three projects of the corpus the code imports nothing from
`tests/`, read and not run, so the examples see the same code on that tree; and that two gates that
catch the same trick by different means are worth more than one, since `protected-paths` reads the
paths of the patch and `existing-tests` runs the code.

## Alternatives considered

- **(a) The tests of the patch.** The two cases of *edits tests* would be caught only by
  `protected-paths`, and a patch that edits a test where the contract does not look would leave
  `existing-tests` running the test it changed.
- **(c) Both versions, warning when they differ.** It doubles the time of the tests, about four
  minutes more for mdformat, to tell what the version of the base already tells.
- **The tests of an authorised file that disappear do not count.** Emptying an authorised file
  would pass unseen.
- **They give `FAIL`.** Renaming or reorganising an authorised file would fail, and the
  authorisation would not allow removing a test.

## Consequences

- The code of the patch is still imported in the process of pytest, and it can rewrite the
  results without a `conftest.py`, for instance with a hook installed when it is imported; so
  `existing-tests` still resists T1 and part of T2 and no more
  ([ADR-0010](0010-threat-model.md)). Restoring the tests and their configuration closes the hole
  that BenchJack showed in SWE-bench; it is not a defence against hostile code.
- The port of the project repository has to compose the paths of the tests of the base over a
  tree, the base with the patch applied, and not only over a commit. This widens the debt of an
  operation of the port that gives the tree of a commit.
- A contract that authorises a test file can still lose tests through it, and a person sees it as
  `ASK`.
