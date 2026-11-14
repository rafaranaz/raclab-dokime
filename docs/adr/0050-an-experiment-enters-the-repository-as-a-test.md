# ADR-0050 · An experiment enters the repository as a test

**Status:** accepted

## Context

The ADRs of A2 rest on measurements made outside the repository. ADR-0043 quotes the program that
loads a container; ADR-0044 says that its rule of order was written in 25 lines of Python and
compared with `git rev-list` on six repositories; ADR-0045 describes a reader of reports, the
opening of a path without links and a reader in a process of its own. None of those programs, and
none of the repositories built for the tests, is in the repository. No workflow runs `docker` or
`podman`, so the four guarantees of ADR-0043 are not checked by CI.

## Decision

A measurement that a decision rests on enters the repository as a test or a fixture of the scope
it belongs to, when that scope opens, with its requirement. The basis of the ADR gives the result
and names the test, or says that it is still to come and in which scope. A program is not kept as
prose in the basis. The adr skill says so in its section on the basis.

## Basis

Read in the repository on 2026-11-14: one ADR quotes a program, two describe programs that are not
in the repository, and no workflow uses an engine. Reasoning, without a test: that a measurement
kept as prose is not run again when the code or the engine changes, and a test is. The test that
would confirm it is in the scopes of A2: the rule of order in `packs`, the reader in `sandbox` and
the guarantees of ADR-0043 in the CI of `sandbox`, each checked again by every pull request.

## Alternatives considered

- **Keep the programs in the basis**, as ADR-0043 does. They are read, not run, and nothing says
  when they stop being true.
- **A directory of experiments outside the scopes.** It would hold code that no gate runs and no
  requirement asks for.
- **Link to the program somewhere else**, such as a gist or the working directory of a session. It
  leaves the repository, and the link can break.

## Consequences

- ADR-0043, ADR-0044 and ADR-0045 are accepted and are not rewritten. Their programs enter as tests
  when `sandbox` and `packs` open: the load program, the rule of order with its repositories, the
  reader with its hostile reports.
- A test of an engine needs the engine in CI. One that is skipped because no engine is there has to
  fail, not pass in silence; that is a requirement of `sandbox`.
- An ADR may now say that its measurement is still to come. That is honest only if the scope that
  will hold it is named.
