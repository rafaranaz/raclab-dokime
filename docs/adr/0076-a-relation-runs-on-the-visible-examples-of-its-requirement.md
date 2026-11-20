# ADR-0076 · A relation runs on the visible examples of its requirement

**Status:** proposed

## Context

[ADR-0039](0039-what-a-contract-of-the-first-version-may-say.md) opened the catalogue of relations
with `idempotent` and `order-insensitive`. A relation has `id`, `requirement`, `relation` and
`target`, and `order-insensitive` also has `over`, the input whose order does not matter. The first
version checks their shape, and they run from block B. A relation is a check of origin `derived`
([ADR-0013](0013-provenance-decides-what-a-check-can-do.md)): approved by a person and applied
mechanically, and it fails when it does not hold. The gate `relations` of the state `verifying`
runs them, and B2 builds it.

What a relation runs on is not decided anywhere:

- **the inputs it starts from**, since a contract gives no types from which inputs could be
  generated;
- **what `idempotent` means** at `function` with more than one argument, or at `cli`, where the
  output can come back as the standard input or as the files written;
- **how `over` names an input**, today any text of one line;
- **how many permutations** `order-insensitive` tries, and with which seed;
- **what the agent is told** when a relation does not hold, and **what the evidence records**, since
  the predicate v0.3 ([ADR-0075](0075-the-predicate-v0-3-records-the-hold-out.md)) has no place for
  the seed of the relations nor for the orders that failed.

## Decision

**The rule.** A relation runs on the visible approved examples of its requirement and its target,
through a channel that the relation declares and that is never deduced; its follow-up cases are
drawn with a seed that is recorded, and its failure tells the agent where without giving an input.

**The mechanism in B2.**

- **The source cases** are the visible examples of the requirement of the relation, at its target,
  of one step each. An example of more than one step is not a source. A held-out example is never
  a source, since the gate `relations` runs where the key may not be.
- **`idempotent` declares its channel.**
  - At `cli`, the field `via` says `stdout`, so that the standard output of the source run comes
    back as the standard input of a second run with the same arguments, or `files`, so that the
    second run, with the same arguments, runs on the files that the first one wrote.
  - At `function`, `over` names the argument that receives the return of the source call. A
    function with one argument needs no `over`; with more than one, `contract check` refuses the
    relation without it.
  - The relation holds when the second run gives what the first gave: the return, or the exit code
    and the standard output, or the files written.
  - A source whose run raises, or exits with a code other than zero, has no follow-up.
- **`over` names an input.** At `function` it is `args[N]`, the argument at that position from
  zero, or the name of a keyword argument; for `order-insensitive`, what is permuted are the items
  of the list that the source example gives in that argument, and a source whose value there is not
  a list has no follow-up. At `cli`, for `order-insensitive`, it is `stdin`, whose lines are
  permuted, or the name of a file of the input, whose lines are permuted. `contract check` refuses
  an `over` that names no input of the boundary of the target.
- **`order-insensitive` permutes with a seed.** The follow-ups of a source are inputs, distinct from
  each other and from the input of the source, since repeated items make two permutations give the
  same input and can make the reversed order equal to the source. They are the reversed order,
  always when it differs from the source, and up to `relations.permutations` other distinct inputs
  drawn with the seed, 10 unless the policy says otherwise
  ([ADR-0054](0054-the-policy-is-an-optional-file-of-values.md)); the bound is the number of
  distinct inputs that the items allow, not n!. A source whose items allow no other input has no
  follow-up. The relation holds when each follow-up gives what the source gave.
- **The seed** of the relations is a natural integer of 53 random bits from the randomness of the
  system, drawn for each audit and recorded in its ledger.
- **A relation with no source** is a finding `relation-without-source` of the verdict `ASK`: the
  contract asks for a check that no example can feed. That is so when no example is left as a
  source, whether because no visible example of one step has the requirement and the target, or
  because each of them has no follow-up: its run raises or exits with a code other than zero, for
  `idempotent`, or its input named by `over` is not a list or allows no other input, for
  `order-insensitive`.
- **A relation that does not hold** is a finding `relation-fails` of the verdict `FAIL`, at the
  line of the relation, whose message gives the requirement, the relation and the id of the
  visible source example, and neither the permutation nor any value.
- **The evidence** writes the predicate
  `https://github.com/rafaranaz/raclab-dokime/attestation/conformance/v0.4`, the closed schema of
  v0.3 with one field added and the rule of ADR-0069 kept. The entry of the gate `relations`, when
  it ran, has `relations`: the `seed`, in clear, since nothing in it is secret, and `failed`, each
  follow-up that did not hold as `{relation, example}`, with `order`, for `order-insensitive`, a
  permutation that gives its input, as a list of indices of the source order. It holds no input and no value.

## Basis

**Verified**, in the sources named:

- Hypothesis runs 100 satisfying cases by default (`max_examples`), fixes its draw with `@seed` or,
  deterministically, with `derandomize`, which is on by default in CI, and on a failure prints the
  minimal failing case after shrinking it, values included; `verbosity=quiet` prints nothing. Its
  ghostwriter `idempotent()` writes the test `f(f(x)) == f(x)` with strategies deduced from types
  ([API reference](https://hypothesis.readthedocs.io/en/latest/reference/api.html),
  [integrations](https://hypothesis.readthedocs.io/en/latest/reference/integrations.html)).
- QuickCheck runs up to 100 tests by default, replays a run from its seed and size, and warns that a
  seed saved by one version does not replay in another, so a case to keep is to be kept as a case;
  it shrinks the counterexample and prints it
  ([QuickCheck 2.19](https://hackage-content.haskell.org/package/QuickCheck-2.19.0.0/docs/Test-QuickCheck.html)).
- Most studies of metamorphic testing take their source cases from random data or from existing
  test suites; three of them found random sources to detect more faults than manually designed
  ones, and combining both to detect them sooner; good relations make the follow-up run as
  different as possible from the source; permutative relations are one of the usual kinds
  ([Segura et al., IEEE TSE 2016](https://eprints.whiterose.ac.uk/110335/1/segura16-tse.pdf), in
  its review of the generation of source test cases).

**Looked for and not found:** a tool that reports the failure of a property without its values.
Hypothesis and QuickCheck do the opposite, since they report to a person.

**Reasoning only:**

- The contract has no types, so inputs cannot be generated without a generator for each target;
  the visible examples are the inputs a person approved. They are the least effective sources by
  the studies above, which is written as a limit.
- `idempotent` has more than one reasonable reading at `cli` and at a function of several
  arguments; a reading deduced by the harness could check something the person did not mean, so
  the relation says it.
- The reversed order is the permutation most likely to show a dependence on order for a short
  input, so it is always tried; the seed widens it, and the policy bounds the cost, since each
  follow-up is a run in the sandbox.
- The source examples are visible, so nothing is secret in the relation; the agent is told the
  example and not the permutation, so that it is not handed a concrete input to special-case.
- The orders that failed are kept as indices, as QuickCheck advises keeping cases and not seeds,
  without writing a value into the evidence.

The test is the measurement of B2: in the corpus, a patch that breaks a relation of a case fails
the gate, and its good patch passes.

## Alternatives considered

- **Generate inputs for each target**, as Hypothesis does from types. The contract would need a
  generator or a type for each input, a change of its format; left as a possible improvement after
  B3, where the corpus shows whether the visible examples are enough.
- **Deduce the channel of `idempotent`** from the expectation of the source, standard output when
  it expects `stdout`, files when it expects `files`. A source that expects both would be
  ambiguous, and the person would not see what is checked.
- **A fixed number of permutations, or all of them.** All of them grow as n!; a fixed number cannot
  be tuned to the cost of a project.
- **Tell the agent the permutation that failed.** It is a concrete input to special-case, and the
  requirement, the relation and the example are enough to look for the dependence on order.
- **Record only the seed, without the orders that failed.** A seed does not replay across versions
  of the generator, which is the warning of QuickCheck.
- **A separate ADR for the predicate v0.4.** The field exists only for this gate and follows from
  its decisions; the maintainer asked for one ADR.

## Consequences

- `contract check` gains the field `via` for `idempotent` and checks `over` against the boundary of
  the target; a contract of the first version with a relation that declares no channel where one is
  needed fails it.
- The policy gains `relations.permutations`, and the cost of the gate grows with the number of
  sources and of permutations.
- A relation can be checked only where a visible example of one step feeds it; a requirement whose
  examples are all held out or of several steps has `relation-without-source`.
- The reader of `evidence` keeps four schemas, one per version.
- The relations check only what the visible examples reach, the weakest sources by the studies; the
  gate says nothing of inputs that no example covers.
