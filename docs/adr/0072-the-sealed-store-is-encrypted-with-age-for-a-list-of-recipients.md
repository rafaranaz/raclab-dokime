# ADR-0072 · The sealed store is encrypted with age for a list of recipients

**Status:** proposed

## Context

Block B keeps the held-out examples of a contract in a sealed store: held-out content "encrypted for
a list of recipients", an encrypted file in the repository
([architecture](../architecture/02-modules.md)). The roadmap left for before B1 the tool that
encrypts it. The list of recipients has at least two: the maintainer and a second recipient that
keeps a copy, so that losing one key does not lose the held-out examples. dokime has one dependency
at run time today, `pyyaml`.

The strategic review at the close of block A compared the options; the maintainer approved this
recommendation. The session that reviews the work researched it first; the decision is the
maintainer's.

## Decision

**The rule.** Held-out content is encrypted with a published format and an established
implementation of it, never with a format of our own, for a list of recipients any of whom can
decrypt it.

**The mechanism in block B, in attended use.**

- **The format is age** (`age-encryption.org/v1`), with recipients given by their public keys.
- **The implementation is `pyrage`**, a dependency of Python pinned in `uv.lock` with its hashes,
  used only inside the adapter of the sealed store, which the
  [table of modules](../architecture/02-modules.md) puts in `platform`.
- **Any recipient decrypts a sealed batch alone**; adding or removing a recipient means encrypting
  the batch again.

## Basis

Verified on 2026-11-18:

- [pyrage](https://pypi.org/project/pyrage/) 1.4.0, published on August 23, 2026, after 1.2.1 to
  1.3.0 between September 2024 and June 2025; its
  [repository](https://github.com/woodruffw/pyrage) is not archived and had commits up to October
  13, 2026. It is the repository of one person. Its wheels are abi3 for Python 3.10 and later, for
  Linux x86_64 and aarch64, macOS and Windows, and the wheel for Linux x86_64 carries a provenance
  attestation in PyPI, published from its workflow `release.yml`.
- Its README encrypts for several recipients in one call: `encrypt(data, [carol, dave,
  alice.to_public()])`, with x25519 and SSH recipients.
- The format has two independent implementations, both released recently:
  [age](https://github.com/FiloSottile/age) v1.3.2 (August 29, 2026), in Go, and
  [rage](https://github.com/str4d/rage) v0.12.1 (July 14, 2026), in Rust, which pyrage binds.
- [SOPS](https://getsops.io/docs/) v3.13.3 (July 2026) supports "YAML, JSON, ENV, INI and BINARY
  formats".

Reasoning, without a test: that a format with a specification and two implementations keeps the
sealed batches readable if pyrage stops being maintained, since the binaries `age` and `rage`
decrypt the same files. The test is to decrypt a batch written by pyrage with the binary `age`,
in B1.

## Alternatives considered

- **The binary `age` behind an adapter of its own.** No dependency of Python, but one more program
  to pin and install, and a subprocess for every batch.
- **SOPS.** It encrypts files for age, PGP and the key services of the clouds, and changes the
  recipients with `sops updatekeys`. It is one more binary and its scope is secrets of
  configuration, which dokime does not need. The research held that it leaves the structure of the
  file in clear, which would show how many examples are held out; that was not found in its
  documentation, which supports a BINARY format.
- **An envelope of our own on `cryptography`.** A format nobody else reads or reviews.
- **git-crypt.** Not examined.

## Consequences

- dokime gets a second dependency at run time, compiled, with wheels for the platforms above; a
  platform without a wheel builds it from source with Rust.
- The maintenance of pyrage depends on one person. If it stops, the adapter can call the binary
  `age` instead without changing the files.
- Only `platform` imports `pyrage`; an import contract of `lint-imports` says so when the adapter
  is built.
- Where the private keys live is decided apart, in the next ADR.
