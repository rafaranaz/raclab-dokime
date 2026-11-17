# `verify`

The gates of a change that arrives already made, and their aggregation. The requirements are in
[`docs/requirements/verify.md`](../../../docs/requirements/verify.md).

- `GateResult(gate, findings)`: what each gate gives; its `verdict` is the summary of its findings,
  `PASS` when it has none.
- `protected_paths(pack, contract, base, patch, repository)`: the gate `protected-paths`. It
  composes the tree of the base and that of the base with the patch, extracts both and compares
  them path by path without following a link: a file by its bytes and whether it is executable, a
  link by its target. A changed test or configuration of the tests is a `FAIL` unless the contract
  names that exact path in `may_modify_tests`; a mixed file counts only when its section changed;
  `.dokime/` is protected whatever the contract says. A patch that does not apply gives the
  `ERROR` of the repository.

- `baseline(contract, policy, base, image, repository, observer, limits)` and
  `visible_examples(pack, contract, base, patch, image, repository, observer, limits)`: they extract the
  base, or the tree of the change (the code of the patch with the tests and their configuration of
  the base, except what the contract authorises, ADR-0058), ask the port that observes for every example of the contract
  with its inputs alone, and compare each one through `oracle`. The base is observed
  `baseline.runs` times, and an example that holds in some runs and not in others asks
  (`example-varies-on-base`) and is listed in `unstable`. Otherwise, on the base, an example of a
  `preserve` requirement that does not hold is a `FAIL`, and one of a `new` or `change` requirement
  that already holds asks. With the patch, an example that does not hold is a `FAIL`, or an `ASK`
  when its origin is `model` (ADR-0013). A finding names the example, its requirement and up to five
  differences, each value quoted within 200 characters. A refusal of a port is the `ERROR` of its
  finding.

- `existing_tests(pack, contract, policy, base, patch, dockerfile, repository, runtime)`: the gate
  `existing-tests`. The tests run on the base `baseline.runs` times; a test counts as passing in
  the baseline only when it passed in every run, and one that varied is left out and listed in
  `unstable`. Then they run once on the tree of the change. A test of the baseline that no longer
  passes, or disappears, is a `FAIL`; one that disappears from a file that the contract authorises
  asks. A test belongs to a file when its class name is the path with `/` as `.` and without `.py`,
  or starts with that and a `.`. Known limit: beside a module `tests/test_a.py`, a test of a
  package `tests/test_a/` counts as of the module.

The tests run on a double of the audited repository held in memory (`tests/verify/doubles.py`), on a double of the runtime that gives the reports listed in a file of
the project, and on a double of the port that observes that answers from a file
of the extracted project,
itself tested against the rule of CORE-099, so that a double that overlays instead of replacing
cannot let the gates pass.
