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
