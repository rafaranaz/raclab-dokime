# Requirements of the `oracle` scope

What the zone of verification observed of an example, compared with what the example expects,
outside the zone ([ADR-0012](../adr/0012-examples-are-observations-at-a-boundary.md),
[ADR-0063](../adr/0063-a-program-of-sandbox-observes-the-examples-inside-the-zone.md)). This
increment compares; splitting the visible from the sealed examples and the relations come in block
B. The oracle runs nothing: it receives an example of the contract and its observation, and the
gate that calls it decides the verdict. Each requirement follows an EARS template and has at least
one test that declares it in its `SDD-EARS:` marker.

An expectation holds as `holds` of `contract` says: an exact value for an equal value of the same
type, and each matcher of [ADR-0039](../adr/0039-what-a-contract-of-the-first-version-may-say.md)
by its rule. The matcher `$ref` and the boundary `http` never reach the oracle: the check of
contracts refuses them with `not-supported-yet`.

## Comparing an example

- **ORACLE-001** When an example is compared with its observation, the oracle shall compare each step of the example with the observation of the step in the same position.
- **ORACLE-002** When every expectation of every step holds, the comparison shall hold and give no difference.
- **ORACLE-003** If an expectation of a step does not hold, then the comparison shall give a difference that names the step, the part, what was expected and what was observed.
- **ORACLE-004** The oracle shall compare only the parts that a step expects.
- **ORACLE-005** If a step was not observed because the example reached its limit of time, then the comparison shall give a difference that names the step and the limit.
- **ORACLE-006** If a step was not observed because the process of the example crashed, then the comparison shall give a difference that names the step, with the signal or the exit code when the observation carries them.
- **ORACLE-007** If the observation is of another example, then the oracle shall reject the comparison with an error that names both.
- **ORACLE-008** If the observation of a step is of a boundary other than that of the example, then the comparison shall give a difference that names the step.

## At the boundary `function`

- **ORACLE-010** When a step expects `returns`, the expectation shall hold when the step returned a value for which it holds.
- **ORACLE-011** If a step that expects `returns` raised an exception or returned a value that JSON cannot hold, then the comparison shall give a difference that says what the step did.
- **ORACLE-063** When a step expects `$repr`, the comparison shall hold only for a value that JSON cannot hold whose `repr` was observed whole and is the text of `$repr` ([ADR-0079](../adr/0079-an-example-at-function-may-call-the-methods-of-an-object.md)).
- **ORACLE-064** If a step that expects `$repr` returned a value of JSON, raised an exception, or returned a value whose `repr` differs, was cut or was not recorded, then the comparison shall give a difference in `returns` that says what the step did, without the `repr` observed.
- **ORACLE-012** If a step that expects `raises` returned, then the comparison shall give a difference that says what it returned.

## The type of an exception

Decided by the maintainer on 2026-11-17, as `pytest.raises` reads it; ADR-0039 says only "the name
of the exception". So a subclass of `TypeError` holds for `TypeError`, a class of the project named
`TypeError` that is not one does not, and `type: Exception` holds for any exception.

- **ORACLE-020** When the expected `type` of an exception has no module, the oracle shall read it as the class of that name in `builtins`.
- **ORACLE-021** When the expected `type` of an exception has a module, the oracle shall read it as the full name it gives.
- **ORACLE-022** When a step expects `raises`, the expected type shall hold when it is the full name of a class of the MRO of the exception observed.
- **ORACLE-023** When a step expects `raises` with a `message`, the expectation shall hold only when the message also holds for the message observed.

## At the boundary `cli`

- **ORACLE-030** When a step expects `exit`, `stdout` or `stderr`, the oracle shall count each as holding when it holds for the exit code, the standard output or the standard error observed.
- **ORACLE-031** When a step expects `files`, the oracle shall count each file expected as holding when it holds for the text of the file of that name that the command wrote.
- **ORACLE-032** If a file that a step expects was not written, then the comparison shall give a difference that names the file.

## Splitting the examples ([ADR-0014](../adr/0014-hidden-checks-are-held-out-approved-examples.md))

A case is the set of examples of one requirement that share a name of case. The split holds out one
example of each case that has two or more, at random with a seed, and keeps the rest visible, so
that every case keeps at least one visible example. Ensuring that the held-out example is of another
partition than the visible ones is decided with the data of B3. An example that was already published,
which the caller finds in the history, is kept visible: it is never drawn, so that the held-out
part of a case is only made of examples that nobody has seen.

- **ORACLE-040** When the examples of a contract are split with a seed, the oracle shall hold out one example of each case that has two examples or more.
- **ORACLE-041** When the examples of a contract are split, the oracle shall keep visible every example that it does not hold out, and give the visible and the held-out examples each in the order of the contract.
- **ORACLE-042** When the examples of a contract are split, the oracle shall choose the example held out of each case with `random.Random(seed).choice` over the examples of the case that it may draw, in the order of the contract, one generator for the contract, case by case in the order in which each case first appears, a case with none to draw taking nothing from the generator, so that the split is drawn again from the seed and the examples kept visible.
- **ORACLE-043** When the examples of a contract are split, the split shall name, in the order of the contract, the requirements that hold out no example.
- **ORACLE-044** If the seed of a split is not an integer of at least 0, then the oracle shall refuse to split with an error that names what it was given.
- **ORACLE-045** When the examples of a contract are split with examples to keep visible, the oracle shall keep each of them visible and choose the example held out of a case of two or more only among its other examples, holding out none from a case where none is left.
- **ORACLE-046** When the examples of a contract are split, the split shall name, in the order of the contract, each case that holds out no example, by its requirement and its name.
- **ORACLE-047** If an example to keep visible is not an example of the contract, then the oracle shall refuse to split with an error that names it.

## Words for the agent on a held-out failure ([ADR-0014](../adr/0014-hidden-checks-are-held-out-approved-examples.md))

- **ORACLE-050** When the comparison of a held-out example does not hold, the oracle shall word for the agent one line that names the requirement of the example and the classes of its differences, without any value, input or identifier of the example.
- **ORACLE-051** The oracle shall give as the class of a difference its part, with `files` for every file expected and, for a step that was not observed, `time-limit` or `crashed`.

## The follow-ups of a relation ([ADR-0076](../adr/0076-a-relation-runs-on-the-visible-examples-of-its-requirement.md))

A relation runs on the visible examples of its requirement at its target. From the input and the
observation of a source, the oracle builds the inputs of its follow-ups and says whether each
follow-up gives what the source gave. It runs nothing and draws only from the seed it is given, so
the same seed gives the same follow-ups.

- **ORACLE-052** When it is given the items that `order-insensitive` permutes, a seed and a number of permutations, the oracle shall give the follow-up orders: the reversed order first when it gives another input, then up to that number of other orders drawn with the seed.
- **ORACLE-053** The follow-up orders that the oracle gives shall give inputs distinct from each other and from the input of the source, and no more of them than the distinct inputs that the items allow, the source left out.
- **ORACLE-054** When it is given the same items, the same seed and the same number, the oracle shall give the same follow-up orders in the same order.
- **ORACLE-055** When the input named by `over` is a list at `function`, or a text at `cli`, the oracle shall permute its items, which at `cli` are its lines, keeping a final line break where the source has one.
- **ORACLE-056** If the input named by `over` is absent, or is not a list at `function` or a text at `cli`, then the oracle shall give no follow-up for that source.
- **ORACLE-057** When it is asked the follow-up of `idempotent` at `function`, the oracle shall give the input of the source with the argument named by `over`, or its only argument, replaced by the value that the source returned.
- **ORACLE-058** When it is asked the follow-up of `idempotent` at `cli`, the oracle shall give the input of the source with `stdin` replaced by the standard output of the source run for `via: stdout`, or with its files replaced and completed by the files that the source run wrote for `via: files`.
- **ORACLE-059** If the source run raised, exited with a code other than zero or did not complete, then the oracle shall give no follow-up of `idempotent` for that source.
- **ORACLE-060** When it compares a follow-up with its source, the oracle shall say that the relation holds when the follow-up gives the same return of the same type, or an exception of the same type, at `function`; the same exit code and standard output for `via: stdout`; the same files written for `via: files`; and the same exit code, standard output and files written for `order-insensitive` at `cli`.
- **ORACLE-062** When it compares a follow-up of `order-insensitive` at `cli` whose `over` names a file, the oracle shall leave that file out of the files compared when each run leaves it as it received it, and compare it when a run rewrites it, so that what is compared is what each run produced and not the input it was given.
- **ORACLE-061** When a relation does not hold, the oracle shall word it for the agent with the requirement, the relation and the id of the source example, and with neither the input of the follow-up nor any value.
