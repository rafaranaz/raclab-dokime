# ADR-0007 · MIT license

**Status:** accepted

## Context

`dokime` was published under the Business Source License 1.1, which protects commercial use for a
period before converting to an open source license. The market for a harness like this is limited
today, and the main value of publishing it is that someone who finds it useful can adopt it,
adapt it or learn from it without friction.

## Decision

`raclab-dokime` is released under the MIT license.

## Alternatives considered

- **Business Source License 1.1, as in `dokime`.** It protects a commercial opportunity that does
  not exist today at the cost of discouraging adoption and contributions.
- **Apache License 2.0.** Equally permissive and with an explicit patent grant, but longer and with
  more obligations for whoever redistributes it; MIT is enough for the goal of maximum reuse.

## Consequences

- Anyone can use, modify and redistribute the code, including commercially, as long as the
  copyright notice is kept.
- Moving to a more restrictive license later would only apply to new code, not to what has
  already been published under MIT.
