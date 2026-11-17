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
  gate listed twice, and a check of an unknown origin or of no checks.
- `statement(run)`: the in-toto Statement v1 alone, without an envelope. The subjects are the tree,
  by `gitTree`, and the patch, by `sha256`. The predicate v0.1 leaves out every field the run does
  not fill. The whole message of a finding goes to `untrusted`, with the label `message`, cut at
  4096 characters; the code, the verdict and the lines are what dokime fixes. A text the evidence
  quotes by itself, such as the name of a test, is cut at 200 (ADR-0066).
- `not_checked(run)`: what was not checked, by code in the order of ADR-0064: `no-holdout` for each
  requirement, `requirement-without-example`, `only-model-checks`, `test-excluded-unstable` with the
  name of the test untrusted, `example-unstable`, and `outside-threat-model` for each of
  `existing-tests`, `baseline` and `visible-examples` that ran.

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
  those of the types of `core`.

Signing and verifying an evidence file come with block E.
