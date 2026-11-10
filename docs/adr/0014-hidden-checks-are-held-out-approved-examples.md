# ADR-0014 · Hidden checks are approved examples held out by case, plus approved relations

**Status:** accepted

## Context

A hidden oracle defeats solutions fitted to the visible checks. "The same examples with other
values" needs someone to know the correct output for the new values; if a model computes it, the
decisive gate is written by a model that nobody reviews.

## Decision

- The person approves **all** examples. When the contract is approved, the harness holds out part
  of them at random, with a seed kept in the sealed file. The person does not choose which.
- From that split on, the content of the held-out examples exists only encrypted: the clear copies
  are removed from the contract files, and the ledger keeps their digest, not their content.
  Before the split the whole set is in clear where the contract is specified;
  [ADR-0020](0020-agent-isolation-is-optional-adoption-is-a-ladder.md) and
  [ADR-0022](0022-model-calls-of-the-harness-go-through-a-port.md) say what protects it then.
- Hold-out is by case: every case keeps at least one visible example; only cases with two or more
  examples give one to the hold-out. A requirement with no repeated case has no hold-out, and the
  evidence says so.
- A person may also approve **relations** from a closed catalogue, stated in plain language
  ("the order of the lines does not change the total"). The harness applies them mechanically to
  new inputs generated with a recorded seed.
- Sealed checks run only when the visible ones pass. Each sealed batch carries a canary: an
  example whose expected value is wrong on purpose; if it passes, the pipeline is broken.
- Nothing written into the work session contains held-out content. On a sealed failure the agent
  receives the requirement and the class of failure, never values; the list of tests at risk and
  any other feedback carry none either.
- The output of a sealed run is not printed in logs.

## Basis

Literature and reasoning. Visible-versus-held-out gaps and compositional failures
([SpecBench](https://arxiv.org/abs/2605.21384)); allowing several submissions raises cheating from
33 % to 38 %, and hiding tests lowers legitimate performance
([ImpossibleBench](https://arxiv.org/abs/2510.20270)). The hold-out rule by case is reasoning, to
be measured.

## Alternatives considered

- **Variants with an output estimated by a model.** See the context.
- **Random hold-out of a fixed share.** It may hide the only example that explains a case.

## Consequences

- At least two examples per case are needed for a hold-out; tables of rows keep that cheap.
- The agent no longer sees every example: it sees every requirement and every case.
