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

The tests run on a double of the audited repository held in memory (`tests/verify/doubles.py`),
itself tested against the rule of CORE-099, so that a double that overlays instead of replacing
cannot let the gates pass.
