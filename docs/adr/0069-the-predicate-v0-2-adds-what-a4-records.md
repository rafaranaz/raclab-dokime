# ADR-0069 · The predicate v0.2 adds what A4 records

**Status:** proposed

## Context

[ADR-0064](0064-the-evidence-of-a3-is-an-unsigned-statement-with-a-closed-predicate.md) fixed the
predicate v0.1, amended by
[ADR-0065](0065-the-evidence-of-a3-lists-every-gate-of-the-audit-flow.md) and
[ADR-0066](0066-the-untrusted-texts-of-the-evidence-are-bounded.md); it says that a block that adds a
field changes the version, and that a file of v0.1 stays readable as such. A4 has four things to
record that v0.1 has no place for:

- **the image of the change**: `visible-examples` observes in an image built with the tree of the
  change, whose digest A3 keeps only in the ledger;
- **the runs of the verification**, once the gate `repeatability` runs it as many times as
  `verification.runs` of the policy says;
- **the commit of the harness**
  ([ADR-0068](0068-the-harness-is-named-by-its-version-and-its-commit.md));
- **a trusted message for each finding**, which the fine separation of the messages fills later;
  until then the whole message stays in `untrusted`.

The roadmap asked that these go in one version, so that the version changes once.

## Decision

**The rule.** A version of the predicate only adds fields: it never changes what a field of an
earlier version means, and a file is read with the schema of its own version.

**The mechanism in A4.** The predicate type
`https://github.com/rafaranaz/raclab-dokime/attestation/conformance/v0.2` is the closed schema of
v0.1 with four fields added, each absent when the run does not fill it, never `null`:

| Field | What it holds |
|---|---|
| `verifier.commit` | The commit of the harness, 40 lowercase hexadecimal characters. |
| `inputs.change_image` | The image of the change in which `visible-examples` observed: `digest`, and `platform` when its base image has one. |
| `repeated` | `runs`, how many times the verification ran, and `consistent`, whether every run gave the same verdict, as the architecture names it. |
| `message` of a finding | The words of dokime only, trusted and optional. No module fills it in A4; the whole message is still in `untrusted`. |

- `evidence` writes v0.2 from A4 on.
- Its reader reads a file of v0.1 with the schema of v0.1 and a file of v0.2 with that of v0.2,
  and refuses any other predicate type.

## Basis

Reasoning, without a test: adding fields keeps every older file readable, and a field that no module
fills yet, `message`, keeps the fine separation from changing the version again when it comes. The
test is the reader, which reads back a file of each version.

## Alternatives considered

- **v0.2 without `message`, and a v0.3 with it when the fine separation comes.** The version would
  change twice, which the roadmap asked to avoid.
- **The image of the change in place of `inputs.image`.** It would change what a field of v0.1
  means, and `baseline` and the environment use the image of the base.
- **Each new value as an informative field**, `informative` of the architecture, without a new
  version. A gate cannot read an informative field, and these values change what the evidence says
  was checked.

## Consequences

- The reader of `evidence` keeps two schemas, one per version.
- A field that no module fills is in the schema: `message` is always absent in A4.
- `repeated` is present only when `repeatability` ran, so the evidence of a run that stopped before
  the verification leaves it out.
