# ADR-0032 · The person works in their language, and the approval signs what was shown

**Status:** proposed

## Context

[ADR-0005](0005-languages.md) fixed that the user works in Spanish or English while internal
artifacts stay in English, and left the boundary to the architecture. The same text in Spanish
costs between 30 % and 59 % more tokens than in English, by one measurement on one passage.

## Decision

- Examples are data and need no translation.
- Requirements are canonical in English. The person is shown a version in their language.
- The approval signs the digest of the canonical contract and records the digest of **what was
  shown**. A difference between the two cannot change a verdict, because the text of the
  requirements does not decide.
- The texts of the harness come from message catalogues. Free answers are stored as written.

## Basis

Reasoning, plus [one measurement of token cost](https://dev.to/savi444/tokens-per-word-gpt-5-vs-claude-vs-gpt-4-measured-across-7-languages-4419),
a weak source. No evidence of lower quality with Spanish input was found.

## Alternatives considered

- **Converse and store in the user's language.** Internal artifacts would mix languages.
- **Translate without recording what was shown.** Nobody could tell later which text the person
  read when approving.

## Consequences

- Every requirement shown needs a translation step, done by a model and labelled as such.
- Message catalogues have to be kept in two languages.
