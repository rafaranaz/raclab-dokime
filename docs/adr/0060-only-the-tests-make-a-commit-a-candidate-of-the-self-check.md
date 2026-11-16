# ADR-0060 · Only the tests make a commit a candidate of the self-check

**Status:** proposed

## Context

The self-check of a pack takes as candidates the commits that change a test and code that is not a
test, and runs the tests of the commit on its parent and on the commit
([ADR-0041](0041-the-environment-of-a-verified-project-is-a-dockerfile.md)). Today a path is a test
when it matches `tests.paths`, and anything else is code (PACKS-020, PACKS-021), so the
configuration of the tests counts as code.
[ADR-0056](0056-the-pack-names-the-configuration-of-its-tests.md) adds `tests.config` and leaves
open how the self-check counts a commit that changes only configuration and code;
[ADR-0059](0059-a-mixed-file-protects-the-section-that-configures-the-tests.md) adds the pytest
section of a mixed file.

## Decision

This amends ADR-0041 in the rule of a candidate and in how the side of the parent is composed.

- **Only the paths of `tests.paths` make a commit a candidate.** A candidate changes a test and
  code; the files of `tests.config` are neither, so a commit that changes only configuration and
  code is not a candidate.
- **A commit that changes the pytest section of a mixed file is not a candidate.** The side of the
  parent would have to take that section from the commit, which means rewriting part of a TOML or
  INI file in a tree; leaving the commit out avoids it.
- **The side of the parent takes from the commit its tests and the files of `tests.config`**, so
  that the code is the only thing that tells the two sides apart. Those are whole paths, which
  `compose_with_paths` already composes. This changes PACKS-061, which takes only the tests.

## Basis

Reasoning, without a test: a change of configuration can turn a test green without fixing anything,
for instance by no longer turning a warning into an error, and it can hide a test, by excluding it
or marking it `xfail`. If the configuration counted as code, or stayed at the version of the parent
on its side, such a commit could be a witness that proves nothing about the environment. With the
configuration of the commit on both sides, a test that goes from red to green does so because of the
code.

## Alternatives considered

- **Keep the configuration as code**, as today. A commit that changes a test and its configuration
  and nothing else would be a candidate, and the configuration could make it a false witness.
- **Count the configuration as a test.** A commit that changes only configuration and code would be
  a candidate, with nothing in its tests to go from red to green but what the configuration selects.
- **Compose the pytest section of a mixed file on the side of the parent.** It keeps those commits
  as candidates, at the cost of rewriting TOML and INI inside a tree.

## Consequences

- PACKS-030, PACKS-031 and PACKS-061 change when the field `tests.config` and the sections of
  ADR-0059 are built in A3.
- The packs of the corpus can have other candidates once they declare their configuration, so the
  job `corpus` measures them again then.
- Commits that change the pytest section of a mixed file are lost as candidates; how many is not
  measured.
