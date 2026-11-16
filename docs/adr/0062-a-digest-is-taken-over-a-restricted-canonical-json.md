# ADR-0062 · A digest is taken over a restricted canonical JSON, and a hashed record is kept in it

**Status:** accepted

## Context

Three things of block A are identified by a digest of a value: each event of the ledger stores the
hash of the previous one ([ADR-0023](0023-evidence-is-an-attestation-bound-to-the-tree.md)), the
evidence records the policy by the digest of its normalised form
([ADR-0054](0054-the-policy-is-an-optional-file-of-values.md)), and the digest of a contract is
taken over the canonical forms of its parts
([`03-data-and-evidence.md`](../architecture/03-data-and-evidence.md#the-digest-of-a-contract)).
None of them says what the canonical form is, and no code computes it. Two programs that turn the
same value into different bytes give different digests, and a chain or a digest that another
program cannot recompute cannot be verified without the harness.

## Decision

- **The canonical form of a value is its JSON text by RFC 8785 (JCS), restricted.** The keys of
  every mapping are ordered by their UTF-16 code units; there are no spaces; characters that are
  not ASCII are written as themselves, not escaped.
- **The restriction is the values of I-JSON (RFC 7493) without decimals**: texts, whole numbers,
  booleans, null, lists and mappings with text keys. A number that is not whole, a whole number
  outside ±(2^53 − 1), or a text with a lone surrogate of UTF-16 is refused, not rounded nor
  replaced.
- **A digest is `sha256:` and the hexadecimal SHA-256 of the canonical form in UTF-8.**
- **The canonical form is written in the harness**, in `core`, without the package `rfc8785`.
- **A record that is hashed is kept in its canonical form, and a verifier refuses any other
  encoding.** For the ledger, each line is exactly the canonical form of its event with its
  `hash`, and the `hash` is the digest of the event without that field; a line that parses to the
  same event but differs in its bytes is refused. So there are never two encodings of one event.

## Basis

Read:

- DSSE, the envelope that in-toto uses, avoids canonicalisation "for security": the verifier
  checks the bytes as they were signed, before parsing them. It left the older scheme of TUF and
  in-toto because it depended on canonical JSON, where "two semantically different payloads could
  have the same canonical encoding" and the verifier has to parse before it verifies
  ([DSSE, background](https://github.com/secure-systems-lab/dsse/blob/master/background.md)). The
  last rule of the decision answers that for the ledger: the verifier compares bytes.
- The implementation of RFC 8785 by Trail of Bits orders the keys with `encode("utf-16be")`,
  refuses whole numbers outside ±(2^53 − 1) citing the appendix B of the RFC, and refuses lone
  surrogates when it encodes to UTF-8
  ([rfc8785.py](https://github.com/trailofbits/rfc8785.py/blob/main/src/rfc8785/_impl.py)).
- Found by the session that reviews the work, not checked further: implementations of a subset of
  JCS that refuse decimals, as this one does. [MPP.JCS](https://mpp.hexdocs.pm/MPP.JCS.html), in
  Elixir, is a subset of JCS without decimals; [jcs of
  musereel-sdk](https://pkg.go.dev/github.com/emiya-dev/musereel-sdk/jcs), in Go, accepts whole
  numbers and texts and refuses duplicate keys, decimals and lone surrogates.

The tests of the canonical form use the vectors of RFC 8785 that apply to the restriction: the
strings of section 3.2.2 and the order of keys of section 3.2.3; the appendix B is about numbers
with decimals and does not apply. They come with the scope `core`.

Reasoning, without a test: that no value the harness hashes in block A needs a decimal, so leaving
the numbers of ECMAScript out removes the hardest part of JCS without losing anything; and that
Python orders keys by code points, which differs from UTF-16 only for characters outside the basic
plane, so the difference has to be written and tested, not assumed away.

## Alternatives considered

- **`json.dumps` with `sort_keys=True`.** It is not a standard, its order of keys differs from
  JCS outside the basic plane, and another program could not be sure to reproduce a digest.
- **CBOR with the deterministic encoding of RFC 8949, section 4.2.** It is binary, a ledger in it
  cannot be read as text, and it adds a dependency.
- **The package `rfc8785`.** One more dependency for a function of a few dozen lines once
  decimals are out.
- **For the ledger, hash the bytes of each line and drop the field `hash`.** It avoids
  canonicalisation for the chain, as DSSE does, but each event would no longer store its own hash,
  which ADR-0023 decides; it would need to amend it.

## Consequences

- The ledger, the policy and the contract share one function of `core`, and a program outside the
  harness can recompute their digests with any implementation of JCS, within the restriction.
- A value with a decimal cannot be hashed; a later block that needs one decides it then.
- A ledger edited by hand, even only in its spaces, is refused by its verifier.
- The reader of the ledger compares each line with the canonical form of what it parsed, so it
  parses before it verifies; the comparison of bytes is what keeps that from being a surface.
