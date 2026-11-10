# ADR-0030 · The harness is measured on a corpus with known verdicts

**Status:** proposed

## Context

A tool whose job is to keep bad changes out has to know how many it lets through. Public
benchmarks are not a safe yardstick: the reference one was retired because many of its tests
rejected correct solutions and models had seen its data.

## Decision

- A module, `bench`, runs the harness in audit mode on cases with a known verdict: good patches;
  patches that fail visible examples; overfitted patches; the four measured cheating techniques
  (editing tests, special cases, overloaded comparison, state between calls); regressions; a good
  patch in an environment with an unstable test.
- Metrics: false accepts per label (the main one), false rejects, rate of questions, value of the
  hold-out (false accepts on overfitted patches with and without it), stability between two runs,
  minutes of a person per change.
- Each block has a number as its exit criterion, and the results are published with each version.
- Starting size: about thirty cases on three small Python repositories. It grows with every patch
  an agent produces and a person labels.
- The strengths of the design are invariants, each with a mechanism that fails in CI.

## Basis

Reasoning, and [OpenAI's audit of SWE-bench Verified](https://openai.com/index/why-we-no-longer-evaluate-swe-bench-verified/)
for not relying on a public benchmark.

## Alternatives considered

- **Qualitative exit criteria.** "It works" is an impression.
- **A public benchmark as the yardstick.** See the context.

## Consequences

- The corpus has to be written by hand at first.
- A bad published result is still published.
