# ADR-0015 · A gate returns one of four verdicts

**Status:** proposed

## Context

With two verdicts, a doubtful result has to be approved or rejected, and a failure of the
environment counts as a failure of the change.

## Decision

- A gate returns `PASS`, `FAIL`, `ASK` or `ERROR`.
- `ERROR` means the gate could not evaluate. It is retried once; if it persists, a person is
  asked. The person can repair the environment and run the gate again, or abandon the change;
  nobody can accept the error. It never passes, and it does not mark the change as bad.
- A gate is skipped only when the policy declares it optional. Skipping a mandatory gate is an
  `ERROR`. The skipped gates are listed in the evidence and in the pull request.
- Aggregation by precedence: any unresolved `ERROR` gives `ERROR`; else any `FAIL` gives `FAIL`
  and the `ASK` of that round are dropped; else any `ASK` gives `ASK`; else `PASS`.
- A change is delivered with `PASS`, or with `ASK` when a person has answered every question. A
  question raised by a gate is answered by a person; a delegated answer does not count
  ([ADR-0025](0025-the-interview-works-on-files-and-ends-by-coverage.md)). The answers are part of
  the evidence.

## Basis

Reasoning. It keeps the rule that what cannot be evaluated does not pass, without blaming the
change for an unrelated failure.

## Alternatives considered

- **Two verdicts, and a gate that cannot evaluate rejects.** Flaky infrastructure would consume
  attempts and reject good changes.
- **Three verdicts without `ERROR`.** The person could not tell a doubt about the change from a
  broken environment.

## Consequences

- Every consumer of a verdict has to handle four cases.
- In a mode without questions, reaching a question ends the run as pending a person, with that
  reason. It neither rejects nor passes: the check of the pull request stays pending until a
  person answers and the run is repeated.
