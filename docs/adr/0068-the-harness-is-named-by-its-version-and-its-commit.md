# ADR-0068 · The harness is named by its version and its commit

**Status:** accepted

## Context

The evidence records the version of the harness that produced it
([ADR-0064](0064-the-evidence-of-a3-is-an-unsigned-statement-with-a-closed-predicate.md)). The
version is `0.0.0` in `pyproject.toml`, the same for every commit, so two runs of different code
say the same. A4 ends with version 0.1, and the roadmap left for before A4 how the harness is
versioned and published. In A4 the harness audits the pull requests of this repository, running
from its own checkout in CI.

## Decision

**The rule.** The evidence names without ambiguity the code of the harness that produced it.

**The mechanism in A4.**

- **The version is written by hand** in `pyproject.toml`, the project `raclab-dokime`. It goes to
  `0.1.0` when A4 closes, with the tag `v0.1.0` on that commit.
- **The evidence also records the commit of the harness**, since every commit between two versions
  has the same version
  ([ADR-0069](0069-the-predicate-v0-2-adds-what-a4-records.md)).
- **The harness is not published in A4.** The workflow of the audit runs it from the checkout of
  this repository. It is published, with the attestations of the package index, when someone
  outside this repository uses it.

## Basis

Verified:

- setuptools-scm and hatch-vcs take the version from the tags of git, with `dynamic = ["version"]`
  in `pyproject.toml`
  ([setuptools-scm](https://setuptools-scm.readthedocs.io/en/stable/)).
- PyPI makes PEP 740 attestations by default for a project that publishes from GitHub Actions with
  Trusted Publishing and `pypa/gh-action-pypi-publish` from 1.11
  ([PyPI](https://blog.pypi.org/posts/2024-11-14-pypi-now-supports-digital-attestations/),
  [its documentation](https://docs.pypi.org/attestations/)).

Looked for and not found: whether the backend of this repository, `uv_build`, takes a version from
the tags of git.

Reasoning, without a test: that a version and a commit name the code without ambiguity, and that a
version by hand costs one line at each release. The test is the evidence of the first pull request
of A4, which has to name both.

## Alternatives considered

- **The version from the tags of git**, with setuptools-scm or hatch-vcs. It needs another backend
  of the build, and every commit between two tags gets a version of its own, which the commit in the
  evidence already gives.
- **Publish 0.1 in PyPI**, with Trusted Publishing and its attestations. Nobody outside this
  repository uses the harness yet, and a published name is hard to take back.
- **Only the version, without the commit.** Every commit between two versions would say the same.

## Consequences

- Raising the version is a commit of its own at the close of a milestone that releases one.
- The evidence carries one more field, the commit, which needs the next version of the predicate.
- A harness that does not run from a checkout of git has no commit to record; the evidence leaves
  the field out, as it leaves out what a run does not reach.
