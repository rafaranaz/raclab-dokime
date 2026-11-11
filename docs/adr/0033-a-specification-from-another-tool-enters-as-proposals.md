# ADR-0033 · A specification from another tool enters as proposals

**Status:** proposed

## Context

Some users already write specifications with another tool before they meet this one. Asking them
to write their requirements again is friction with no benefit. Accepting those specifications as
contracts would be worse: a contract is what a person approved, with examples that decide
([ADR-0011](0011-contract-of-requirements-and-approved-examples.md)).

## Decision

- A command reads a specification made with another tool and turns its requirements into
  **proposed** requirements of a contract.
- Importing approves nothing. The person reviews what was imported, the examples are added, and
  the contract is approved with its signature like any other.
- Each requirement records its source: written here, or imported, with the tool and the file it
  came from.
- The format of the contract stays our own. An importer exists per external format, outside the
  module that defines the contract.

## Basis

The requirements file of Kiro holds EARS statements under headings and no concrete examples with
an input and an expected output; this was read in its
[documentation](https://kiro.dev/docs/specs/feature-specs/requirements-first/). The formats of
other tools were not checked for this decision. That an external specification lacks what decides
a verdict here, and so cannot be a contract, is reasoning from that one case and from
[ADR-0012](0012-examples-are-observations-at-a-boundary.md): an example needs a boundary and
matchers from a closed catalogue. The decision is cheap to undo: it adds one field and a command.

## Alternatives considered

- **No import.** The user rewrites the requirements. It costs adoption and protects nothing that
  the approval does not already protect.
- **Adopt an external format as the contract.** The one checked has no examples at a boundary, so
  the part that decides would still need a format of ours.
- **Treat imported requirements as approved.** They were approved for another purpose, without
  examples and without the signature that makes an approval here.

## Consequences

- The contract format carries a `source` field in each requirement.
- Importers arrive with block F, one per format that someone asks for.
- A user of another tool keeps their text and still has to write and approve examples.
