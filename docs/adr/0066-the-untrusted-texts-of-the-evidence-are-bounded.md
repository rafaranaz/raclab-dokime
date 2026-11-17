# ADR-0066 · The untrusted texts of the evidence are bounded

**Status:** proposed

## Context

[ADR-0064](0064-the-evidence-of-a3-is-an-unsigned-statement-with-a-closed-predicate.md) puts in
`untrusted` every text that may carry what dokime did not write: in A3, the whole message of each
finding and the name of each unstable test. As proposed, it cut each such text at 200 characters.
The cut dropped out of the text when the review of #119 replaced the bullet with the whole message
in `untrusted`. That was an error of drafting, not a decision.

Messages are longer than 200 characters. A finding of an example that does not hold quotes up to
five differences, each with its expected and observed value cut at 200 characters, so its message
can reach about 2,200 characters.

The session that reviews the work tried the reader of the evidence on twelve files changed by hand.
One of the files it accepted had an untrusted text of 500 characters.

## Decision

This amends ADR-0064 in the texts of `untrusted`.

- **A text that the evidence quotes by itself**, such as the name of a test (and later a path), has
  at most **200 characters**.
- **The message of a finding**, under the label `message`, has at most **4,096 characters**.
- **The builder cuts a longer text** to one character below its limit, followed by `…`, so that a
  run is never refused for the length of what it quotes.
- **The reader refuses a longer text** with an `evidence-schema` finding that names its place.
- **A character is a code point of Unicode**, as the canonical form of
  [ADR-0062](0062-a-digest-is-taken-over-a-restricted-canonical-json.md) writes it.

## Basis

Reasoning, without a test:

- **200 characters** is the limit that `verify` already applies to each value it quotes.
- **4,096 characters** holds the longest message of the gates of A3, about 2,200, with room to
  spare.
- **The limits keep the evidence small enough to be shown** in a pull request in A4.

## Alternatives considered

- **200 characters for every text, the message included.** It cuts off the differences that
  explain why an example fails.
- **No limit.** A test name or an observed value can be as long as the code under test makes it,
  and the evidence goes to pull requests.
- **The builder refuses a text that is too long, instead of cutting it.** A run would end without
  evidence because of something the code under test wrote.

## Consequences

- A long message loses its end in the evidence.
- The reader can refuse a file whose texts were made longer by hand.
