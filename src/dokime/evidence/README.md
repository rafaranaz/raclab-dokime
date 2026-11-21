# `evidence`

The evidence of a run, as
[ADR-0064](../../../docs/adr/0064-the-evidence-of-a3-is-an-unsigned-statement-with-a-closed-predicate.md)
fixes it for A3. The requirements are in
[`docs/requirements/evidence.md`](../../../docs/requirements/evidence.md). It imports nothing but
`core`, and records the verdicts it is given without deciding any.

- `run.py`: what `evidence` is given, in types of its own. A `Run` has the story, the tree of the
  base with the whole patch, the bytes of the patch, the verdict of the state, the version of the
  harness, the `Inputs` (base, effective policy and, when reached, the image, the bytes of the pack
  and the digest of the program that observes), the gates (`GateRan`, `GateNotApplicable` or
  `GateNotReached`, the eleven of the audit flow of A3 in its order, ADR-0065), the
  head of the ledger before `evidence.built`, and the `Contract` when it was read (the bytes of its
  file and the origins of the examples of each requirement). `interfaces` converts the results of
  `verify` into them.
- `build(run)`: the `Evidence` of a run. Its `name` is `<story>.statement.json`, its `data` is the
  canonical form of ADR-0062 of the statement, and its `digest` is that of the bytes, for the event
  `evidence.built`. It refuses a story, a requirement or an unstable example that is not a name, a
  gate listed twice, a check of an unknown origin or of no checks, and a hold-out on a gate other
  than `sealed-examples`, with a name that is not a name, a digest that is not one or a motive
  other than `single-example` and `all-published`.
- `statement(run)`: the in-toto Statement v1 alone, without an envelope. The subjects are the tree,
  by `gitTree`, and the patch, by `sha256`. The predicate v0.4 (ADR-0076) leaves out every field
  the run does not fill; besides those of v0.1 it has, from v0.2 (ADR-0069), `verifier.commit`,
  the commit of the harness, `inputs.change_image`, the image in which `visible-examples` observed,
  and `repeated`, the runs of the verification and whether they were consistent; and, from v0.3,
  `holdout` on the gate `sealed-examples` when it observed: `batch`, the digest of `sealed.age`,
  `held`, the cases that hold out an example, `kept_visible`, the ids of the examples kept visible
  as already published, and `without_holdout`, the cases that hold out nothing with their motive.
  It holds no id of a held-out example, no input and no value. From v0.4, the gate `relations`,
  when it ran with a record, has `relations`: `seed`, the seed of the audit, and `failed`, each
  follow-up that did not hold as `relation` and `example`, with `order` for `order-insensitive`,
  the indices of the items of the source in the order that failed. No input and no value. It writes no trusted `message` in a finding:
  no module gives one yet. The whole message of a finding goes to `untrusted`, with the label `message`, cut at
  4096 characters; the code, the verdict and the lines are what dokime fixes. A text the evidence
  quotes by itself, such as the name of a test, is cut at 200 (ADR-0066).
- `not_checked(run)`: what was not checked, by code in the order of ADR-0064 and ADR-0075:
  `case-without-holdout` for each case of a sealed run that holds out nothing, with the requirement
  in `what`, the case in `case` and the reason of its motive, `requirement-without-example`,
  `only-model-checks`, `test-excluded-unstable` with the name of the test untrusted,
  `example-unstable`, `outside-threat-model` for each of `existing-tests`, `baseline` and
  `visible-examples` that ran, and `best-effort-secrecy` for each limit of the detection of what was
  published, when the gate `sealed-examples` observed. `no-holdout` is not written in v0.3: it keeps
  its meaning of one entry per requirement in the files of v0.1 and v0.2. A run without the key
  lists nothing of the hold-out, since its gate is not applicable with `the key is not here`.

- `read_back(data)`: the findings of bytes of evidence, none when they meet the schema. Bytes that
  are not JSON of whole numbers give `evidence-not-json`; JSON that is not in the canonical form
  gives `evidence-not-canonical`; and each place that breaks the closed schema of the predicate (an
  unknown field, a missing one, a `null`, a value of another type, list or pattern, a gate listed
  twice) gives an `evidence-schema` that names it, in the order of the statement. So does a
  `predicate/verdict` that is not the precedence of ADR-0015 over the verdicts of the gates that
  ran, or a predicate where no gate ran: the reader checks the verdict written, it decides none.
  The gates have to be those of `AUDIT_GATES`, in its order; a `not-reached` gate has to follow
  one that ran with a verdict other than `PASS`, and no gate runs after it. An untrusted text has
  at most 200 characters, or 4096 for a message. `build` reads its
  own bytes back and refuses a run whose bytes do not meet the schema, such as an empty version of
  the harness or an empty reason. The patterns of digests, commits, trees, verdicts and codes are
  those of the types of `core`. A file is read with the schema of its version: one of v0.1 has none
  of the fields of v0.2, one of v0.2 may carry in a finding a trusted `message` of 1 to 4096
  characters, only one of v0.3 or later may carry `holdout`, on the gate `sealed-examples` alone,
  the code `case-without-holdout` and its field `case`, which it requires, and only one of v0.4
  may carry `relations`, on the gate `relations` alone, whose `order` is the indices from zero of
  its items, each once. A file of v0.4 whose gate `relations` did not run has no `relations` and is
  valid. `tests/evidence/files` keeps a file of v0.1, written by the builder of A3, one of v0.2,
  written by that of A4, and one of v0.3, written by that of B1.

Signing and verifying an evidence file come with block E.

### Replaying the orders of a relation

The evidence writes the seed of the audit, not the seed of each source. The seed of a source is
recomputed from it, as `verify.relations.source_seed` draws it: the first 6 bytes, read as a
big-endian integer, of the SHA-256 of the text `<seed>/<relation>/<example>`, with the seed in
decimal and the ids of the relation and of the source example. With that seed, the items of the
source and `relations.permutations` of the policy, `oracle.relations.orders` gives the same
follow-up orders in the same order; `order` in `failed` names the one that did not hold.

```python
import hashlib


def source_seed(seed: int, relation: str, example: str) -> int:
    drawn = hashlib.sha256(f"{seed}/{relation}/{example}".encode()).digest()
    return int.from_bytes(drawn[:6], "big")
```
