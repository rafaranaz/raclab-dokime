# ADR-0021 · The agent disputes a check instead of editing it

**Status:** proposed

## Context

An agent usually touches a test because it believes the test is wrong, and sometimes it is: a
person can approve a mistaken example, and even curated tests reject correct solutions. Without a
way to say so, the agent either edits the test or bends the code to satisfy it.

## Decision

- The agent may dispute an example, an existing test or a sealed failure ("I believe requirement
  R is met"). It must cite the requirement or the approved example the check contradicts.
- A dispute never changes anything. It opens a question to a person, who then sees the check.
- Approved examples can be disputed too. If the person agrees, the contract is amended: new
  version, new digest, new approval.
- Disputes have a budget that asks when exhausted, and they are counted in the evidence.

## Basis

Literature. Giving the model a way out to ask for human intervention lowered cheating from 54 %
to 9 % for one model family and much less for another
([ImpossibleBench](https://arxiv.org/abs/2510.20270)); 35.5 % of audited benchmark tasks had tests
that rejected correct solutions
([OpenAI](https://openai.com/index/why-we-no-longer-evaluate-swe-bench-verified/)).

## Alternatives considered

- **Approved examples cannot be disputed.** It prevents abuse, and it also hides an approval made
  by mistake.
- **A dispute validated automatically.** Whether two statements contradict each other is a
  judgement about meaning; only the citation and the format can be checked mechanically.

## Consequences

- A weak model may dispute to avoid work; the budget and the count bound it.
- Each accepted dispute restarts the specification of that contract.
