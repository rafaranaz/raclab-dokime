# ADR-0038 · Directives in a contract are marked with a dollar sign

**Status:** accepted

## Context

An example mixes data with instructions to the harness: compare this number with a tolerance,
this text has several lines and no final newline, this output is JSON. Both were written as
mappings (`{approx: 10.03, tolerance: 0.005}`), so an instruction could not be told from data. At
the `function` boundary the data is arbitrary: a function may take or return a mapping with a key
`approx` or `text`. The hand-written contracts of milestone A0 used no matcher, so the collision
did not show.

## Decision

- A mapping with a key that starts with `$` is a **directive**. It has exactly one such key, which
  names the directive; its other keys are its parameters. An unknown directive or parameter is a
  finding.
- Every other mapping is data, exactly as written.
- The list of directives is closed:

| Directive | Parameters | Meaning | Where |
|---|---|---|---|
| `$text` | `final_newline` (mandatory) | A text of several lines, written as a literal block. `final_newline: false` removes the newline that the block adds; `true` keeps it | Inputs and expectations |
| `$json` | — | A text that holds this value written as JSON | Inputs and expectations |
| `$literal` | — | The value is data as written, even if it has keys that start with `$` | Inputs and expectations |
| `$any`, `$approx` (`tolerance`), `$unordered`, `$contains`, `$pattern`, `$ref` | — | The matchers of [ADR-0012](0012-examples-are-observations-at-a-boundary.md) | Expectations only |

- A literal block appears only as the value of `$text`.
- A text that the block cannot express (it ends in several newlines, it has carriage returns or
  spaces at the end of a line) is written on one line, in double quotes, with escapes.

## Basis

Verified: MongoDB marks its operators with `$`, gives `$literal` to treat a value as data, and
discourages field names that start with `$` because some features do not support them. So the
convention exists in a widely used system, with the same escape and with a known cost. Verified
with the prototype of the reader: a key such as `$approx` or `$text` is read as a plain key in
block style and in flow style.

From memory, not checked today: JSON Schema marks its own keywords the same way (`$ref`, `$id`).
Reasoning: a mark in the key is visible to the person who approves, and data with such keys is
rare. No test: the A0 contracts used no matcher. The first contract of the corpus that uses one is
that test.

## Alternatives considered

- **YAML tags (`!approx 10.03`).** They are made for this, but
  [ADR-0037](0037-a-contract-is-read-by-strict-rules-of-its-own.md) forbids tags, parameters do
  not fit a scalar, and fewer people can read them.
- **By position: a matcher is whatever appears inside `expect`.** It does not help where the
  expected value is itself a mapping with that key.
- **Wrap every piece of data (`{value: …}`).** No collision, and every example doubles in size.

## Consequences

- The matchers keep their meaning and change their spelling: `{approx: …}` is `{$approx: …}`.
- Data with a key that starts with `$` has to be wrapped in `$literal`.
- The architecture document and the A0 contracts are rewritten with the directives.
