# `verify`

The gates of a change that arrives already made, and their aggregation. The requirements are in
[`docs/requirements/verify.md`](../../../docs/requirements/verify.md).

- `GateResult(gate, findings, unstable, checks)`: what each gate gives; its `verdict` is the
  summary of its findings, `PASS` when it has none. `checks` has one `Checks(origin, total)` for
  each origin that has checks, in the order `existing`, `human`, `derived`, `model`
  ([ADR-0064](../../../docs/adr/0064-the-evidence-of-a3-is-an-unsigned-statement-with-a-closed-predicate.md)),
  and `checks_of` counts them. The gates of examples count the examples of the contract, and
  `existing-tests` the tests that passed in the baseline. A gate that ends with a refusal gives no
  checks.
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
  finding. Before all of that, a comparison that is not recorded, because a step expects `$repr`
  and the zone did not record the `repr` of what it returned, is `repr-not-recorded`, an `ERROR`
  and the only finding of its example: it says nothing of the change (ADR-0079).

- `existing_tests(pack, contract, policy, base, patch, dockerfile, repository, runtime)`: the gate
  `existing-tests`. The tests run on the base `baseline.runs` times; a test counts as passing in
  the baseline only when it passed in every run, and one that varied is left out and listed in
  `unstable`. Then they run once on the tree of the change. A test of the baseline that no longer
  passes, or disappears, is a `FAIL`; one that disappears from a file that the contract authorises
  asks. A test belongs to a file when its class name is the path with `/` as `.` and without `.py`,
  or starts with that and a `.`. Known limit: beside a module `tests/test_a.py`, a test of a
  package `tests/test_a/` counts as of the module.

- `repeatability(runs)`: the gate `repeatability`. `interfaces` runs the gates of the state
  `verifying` as many times as `verification.runs` of the policy says, and gives it the results of
  each run; a gate whose verdict differs between two runs asks (`verdict-varies`), naming its
  verdict in each run, and runs that do not hold the same gates once each are `runs-differ`, an
  error. Fewer than two runs are refused. The findings follow the gates in the order of the runs.
- `aggregate_state(gates, results, not_applicable)`: the aggregation of the gates of a state
  (ADR-0015, ADR-0034). It lists every gate of the state in its order, run with its result, not
  applicable with where it is built, or, for a gate it builds that the caller gives as not
  applicable, with the reason given, as `sealed-examples` without its key or never sealed; and
  gives the verdict by precedence: `ERROR`, then `FAIL`, which drops the
  `ASK` of the round, then `ASK`, then `PASS`. A built gate without a result, a result of a gate
  outside the state, a gate not in the table of the architecture, or two results of one gate, are
  an `ERROR` of the aggregation.

## The gate `relations`

`relations(pack, contract, base, patch, image, repository, observer, limits, seed, permutations)`
runs each relation of the contract (ADR-0076) and gives a `RelationsOutcome`: the result of the
gate, the seed of the run and each follow-up that did not hold, with its relation, its source and,
for `order-insensitive`, its order. It is in `BUILT`, and runs in the state `verifying`.

- **The sources** of a relation are the visible examples of its requirement at its target that
  have one step; a held-out example is never one.
- **Two observations on the tree of the change**: the sources, then their follow-ups, built by
  `oracle.relations`. The orders of a source are drawn with `source_seed(seed, relation, example)`,
  48 bits of the digest of the seed of the run and the two ids, so that sources of the same length
  do not get the same orders and the same seed gives the same follow-ups.
- **A source not observed to its end** has no follow-up; a follow-up not observed to its end does
  not hold. `holds` gets the input of each run.
- **Findings**: `relation-without-source`, an `ASK`, when no source of a relation has a follow-up;
  `relation-fails`, a `FAIL`, once for each relation and source, with the words of the oracle. Each
  follow-up compared is a check of origin `derived`. A refusal of a port is its finding, an
  `ERROR`, and nothing else.

The tests run on a double of the audited repository held in memory (`tests/verify/doubles.py`), on a double of the runtime that gives the reports listed in a file of
the project, and on a double of the port that observes that answers from a file
of the extracted project,
itself tested against the rule of CORE-099, so that a double that overlays instead of replacing
cannot let the gates pass.

## The sealed batch and the gate `sealed-examples`

The sealed batch is what the sealed store encrypts (ADR-0014, ADR-0072): each held-out example with
its salt and its text as approved, the seed of the split and the canary, in canonical form.

```python
from dokime.verify.sealed import Batch, SealedExample, batch_bytes, make_canary, read_batch

canary = make_canary(contract, seed, canary_id, impossible)  # 32 hexadecimal digits at random
content = batch_bytes(batch)  # Batch(story, base, seed, order, kept_visible, examples, …)
batch = read_batch(content)  # or a RefusalError unreadable-batch

result = sealed_examples(
    pack, contract, text, batch, base, patch, image, repository, history, observer, limits
)
```

- **The canary** copies the held-out example that the seed chooses, with only its first step and,
  as its one expectation, the impossible text, as `stdout` at `cli` or `returns` at `function`. If
  it holds, the gate gives `canary-passed`, an `ERROR`: the comparison accepts what cannot hold,
  the side of a false accept. When it fails, which it has to, it is no finding and no check, so it
  never counts as the failure of a requirement nor reaches the agent.
- **The sentinel** is the impossible text of the canary, which exists only in the batch. Before
  anything is observed, `verify.sentinel` looks for it in the tree of the change extracted for the
  zone, in every path, in the bytes of every file and in the target of every link, never followed,
  and in the JSON of every request. Found, the gate gives `sentinel-in-zone`, an `ERROR` whose
  message does not hold the text, and observes nothing: the hold-out is not sealed, whether the
  agent or the harness put it there. It looks for the text as it is; content transformed on
  purpose is outside the threat model (INV-2, INV-3).
- **The batch is checked before anything is observed**: it has to hold exactly the held-out
  examples of the contract, each with the digest of its salt and its text that the contract gives,
  and each text has to read as the example of its id, requirement and case. The split drawn again
  from the seed, the examples kept visible and the order of the batch has to hold out those
  examples and leave without one the cases the batch names, with their reasons. Otherwise the gate
  gives `sealed-batch-mismatch`, an `ERROR`.
- **The history of the contract** is read through the port `FileHistory`, with `published` of
  `verify.published`, the same function that the command that seals uses: an example is published
  when an example of the list `examples` of a version has its id, or its boundary, target and steps
  as YAML reads them; an entry of `held_out` publishes nothing. A base of the batch out of the
  history of the change, or examples kept visible other than those published from that base, is
  `sealed-batch-mismatch`. A held-out example published in the history of the change is
  `held-out-published`, an `ERROR` at its entry in `held_out`, whose message says to replace it and
  seal again. A refusal of a port, `git-failed` among them, ends the gate in `ERROR`, never in a
  pass. Nothing is observed in any of these cases. The limits of the comparison are those of the
  history: an example published with a field added or a value spelt otherwise is not recognised,
  nor a version under an earlier path or in a commit that the base does not reach, nor a copy in
  another file; and the history is read up to the base of the change, so a held-out example
  published in a commit of the change and taken back in another is seen by the next audit where the
  project merges keeping the commits, by rebase or by a merge commit, and by none after a squash
  merge.
- **Whether the gate applies** is `applicability(holds_out, batched, key)`, from the entries
  `held_out` of the contract and the sealed batch, both of the base, decided before the key: a
  batch without entries is `sealed-batch-mismatch` and entries without a batch
  `sealed-batch-missing`, both `ERROR` and in CI too; neither makes the gate not applicable with
  `NOT_SEALED`, `the contract holds out no example`; and without the key it is not applicable with
  `NOT_HERE`, `the key is not here`. `None` means that the gate runs.
- **The cases without a hidden part** are in the batch with their reason, `single-example` or
  `all-published` (every example of the case was already published, so none was drawn), and
  `unheld_cases(contract, done)` gives them from a split; the evidence shows them.
- **A held-out example that fails** is `sealed-example-fails`, a `FAIL`, or
  `sealed-model-example-fails`, an `ASK`, for one whose origin is `model`, with the words of the
  oracle for the agent: the requirement and the classes of the failure, never a value, an input or
  an identifier. A held-out comparison that is not recorded is `repr-not-recorded`, an `ERROR`
  that names the requirement alone. The canary expects a text, never a `$repr`, so its comparison
  is always recorded.
- **Where the key is not**, the gate is not applicable with the reason `NOT_HERE`, "the key is not
  here". The flow of the audit runs the gate only after `visible-examples` passed.
