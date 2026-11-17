# ADR-0065 · The evidence of A3 lists every gate of the audit flow, reached or not

**Status:** proposed

## Context

[ADR-0064](0064-the-evidence-of-a3-is-an-unsigned-statement-with-a-closed-predicate.md) has the
predicate list "every gate of the state, in its order, as the aggregation lists it", with the
statuses `run` and `not-applicable`. The evidence is of a run, and a run of the audit flow goes
through five states with eleven gates
([`04-states-and-flows.md`](../architecture/04-states-and-flows.md#the-audit-flow)). A run that a
gate stops does not reach the gates after it, and v0.1 has no status for them.

The session that reviews the work tried the reader of the evidence on twelve files changed by hand.
One of the files it accepted had `gates: []` and the verdict `PASS`. The check of the verdict
against the gates that ran, added since, refuses that file. It does not refuse a predicate that
leaves out some gates of the flow, or lists them in another order.

[ADR-0023](0023-evidence-is-an-attestation-bound-to-the-tree.md) and
[`03-data-and-evidence.md`](../architecture/03-data-and-evidence.md#the-evidence) already name four
statuses: `run`, `skipped`, `not-applicable` and `not-reached`. A gate is `not-reached` only in a
run that an earlier gate stopped.

## Decision

This amends ADR-0064 in the gates of the predicate.

- **The gates of the predicate are exactly those of the audit flow of A3, in its order:**
  `contract`, `environment`, `baseline`, `protected-paths`, `existing-tests`, `visible-examples`,
  `relations`, `changed-line-coverage`, `behaviour-differences`, `repeatability` and
  `sealed-examples`. The list is a constant of `evidence`, and the reader refuses any other list of
  names, order or number.
- **The status `not-reached` joins the schema**, with `gate`, `status` and `reason`. A
  `not-reached` gate has to come after a gate that ran with a verdict other than `PASS`, and no gate
  runs after a `not-reached` one. A gate that A3 does not build is `not-applicable`, reached or not.
- **`skipped` stays out of v0.1**, since no gate of A3 is optional in the policy.
- **`interfaces` builds the gates of the run with the same list.** A test of step 11 checks that
  the gates it passes to the aggregation of each state, joined in the order of the states, are the
  constant of `evidence`.

## Basis

The four statuses and the rule of `not-reached` are already in ADR-0023 and in the architecture.
The list of gates is that of the audit flow of the architecture. What is decided here is only that
the evidence of A3 uses them.

Reasoning, without a test: that a list fixed in `evidence` is the check that a stand-alone reader
can make of the gates. ADR-0023 has the verifier check the gates against the flow file, and A3 has
no flow file.

## Alternatives considered

- **`audit` runs every gate it builds even when one fails, so that no gate goes unreached.** It
  contradicts the audit flow, where a `FAIL` goes to `failed`, and it would run the tests of a
  change whose contract has already failed.
- **The reader takes the list of gates from its caller.** The caller that builds the evidence would
  be the one to say which gates it should have, and a stand-alone reader would have no list.
- **Each state lists only its own gates, and the run lists the states it reached.** It needs a field
  for the states, which v0.1 does not have, and leaves the unreached gates unnamed.

## Consequences

- The evidence of a run that stops names every gate it did not reach, with the reason.
- `evidence` holds a second copy of the list of the audit flow, after the architecture. When the
  flow file exists, the list comes from it and the evidence records its digest.
- The runs of the tests of `evidence` list the eleven gates.
- The step 11 test ties the list in `interfaces` to that of `evidence`.
