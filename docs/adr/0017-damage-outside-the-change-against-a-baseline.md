# ADR-0017 · Damage outside the change is found by comparing against a baseline

**Status:** proposed

## Context

A change can meet its contract and break something else. In one study 30 % of the patches of an
open model broke at least one test that passed before.

## Decision

- Before the change, the existing suite and every example run on the base commit, more than once.
  Tests whose result varies are marked unstable, excluded and listed.
- After the change, every test that passed in the baseline must still pass and none may disappear.
- The proportion of changed **production** lines executed by the suite and the examples must reach
  the threshold of the policy. Lines of test code do not count.
- The map of which tests execute which lines comes from the coverage of the baseline. It gives the
  agent a list of tests at risk, and bounds where behaviour differences are looked for.
- For behaviour differences between base and change that no requirement explains, a model groups
  them and proposes an explanation; a person decides.
- The example gates run twice, in new processes and another order; a different result asks.

## Basis

Literature. Telling the agent which tests are at risk lowered regressions from 6.08 % to 1.82 %
([TDAD](https://arxiv.org/abs/2603.17973), 100 cases, one model). Change-directed before/after
tests cover 91 % of changed lines on Python libraries
([DiffTestGen](https://arxiv.org/abs/2607.16024)); deciding whether a difference was intended has
58 % precision with a model ([Testora](https://arxiv.org/abs/2503.18597)), hence the person.

## Alternatives considered

- **A static call graph.** It needs analysis per language inside the kernel and is imprecise in
  dynamic languages. It stays as a deferred hypothesis.
- **Run only the tests related to the change.** It saves time, which is not a criterion here, and
  misses regressions.

## Consequences

- Coverage tooling is required from the language pack for this gate.
- Evidence exists for libraries; for applications with a graphical interface none was found.
