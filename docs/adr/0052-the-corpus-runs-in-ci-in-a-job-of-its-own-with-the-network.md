# ADR-0052 · The corpus runs in CI in a job of its own, with the network

**Status:** accepted

## Context

The exit criterion of A2 is that the packs of the three repositories of the corpus build and pass
their self-check. On 2026-11-15 `dokime env check` passed on cachetools, python-semver and mdformat,
with packs that lived outside the repository. The roadmap says that in block A the corpus runs as
ordinary tests of the repository.

A pack is ours; the code of each project is not, and it is not copied: it is named by its
repository and its commit. Self-checking a pack therefore needs the network three times: to clone
the project, to pull the base image, and to install what the Dockerfile installs, which
[ADR-0041](0041-the-environment-of-a-verified-project-is-a-dockerfile.md) allows while preparing.
The job of tests already pulls two small images for the tests of the guarantees; it fetches no
code of another project and installs no package. The three runs took 21 s, 37 s and 254 s with the
images already in the store.

## Decision

- **Where the packs live.** `tests/corpus/<project>/` holds the `pack.yaml`, the `Dockerfile` and a
  `source.toml` with the address of the repository and the full name of the commit. Nothing of the
  project is copied.
- **How they run.** A test for each project clones the repository with its whole history into a
  temporary directory, runs `dokime env check` at that commit with the pack of `tests/corpus/`, and
  demands `PASS` with no container and no temporary directory left behind.
- **A job of its own.** The tests of the corpus run in a job of CI named `corpus`, in parallel with
  the others, on every pull request and on every push to `main`. It is a gate: a pull request that
  breaks a pack does not merge. Elsewhere the tests of the corpus run only when asked for, so that
  the job of tests and the gates on a machine do not depend on the network beyond what they do
  today.
- **The environments of the corpus are pinned.** Each Dockerfile of the corpus names its base
  image by its digest and installs every package, its dependencies included, at an exact version,
  so that the gate fails only for a change of ours or for the network, and not because a tag moved
  or a new release of a package broke a test of a project. Moving any of them is a deliberate
  change, in a pull request of its own.
- **What is watched.** The job writes its duration and, when it fails, whether the cause was the
  network. Both are reviewed after a few days of use.

## Basis

[ADR-0041](0041-the-environment-of-a-verified-project-is-a-dockerfile.md) records the base image
of a pack and does not require it to be pinned, so that a person can adopt a project with the
Dockerfile it has. That rule is about the packs of the people who use the harness; it does not
stop us from pinning ours, which serve as a gate.

Measured: the three runs of 2026-11-15 and what they fetched (the clones from GitHub, the image
`python:3.13-slim` from Docker Hub, `pytest` and the dependencies of each project from PyPI). Not
measured: the duration with an empty store, which is the case of a fresh runner, and how often the
network fails in CI. Reasoning, without a test: that a job of its own keeps a failure of the network
from blocking the other gates, and that a few days of use are enough to judge its cost.

## Alternatives considered

- **Run the corpus in the job of tests.** Every run of the gates would wait for it, and a failure of
  the network would stop the tests of the code.
- **Run it only on `main`, or on a schedule.** A pull request could break a pack and merge.
- **Copy the code of the projects into the repository.** It is code of others in our repository,
  and a pinned commit says the same.
- **Leave the packs of the corpus unpinned, as ADR-0041 allows.** A new release of `pytest` or a
  move of `python:3.13-slim` could turn the gate red with no change of ours and block every pull
  request until someone looked.
- **Keep a cache of the clones and the images between runs.** It would save time; it is decided
  when the duration is known.

## Consequences

- A pull request waits for the job `corpus` too; it may take minutes.
- A failure of the network makes the job red with no defect in the code. It is reported as such and
  the job can be run again.
- The ruleset of `main` gains a required check, `corpus`, which the maintainer adds in GitHub; the
  list of required checks in the roadmap changes with it.
- Moving a pinned image or package needs a pull request, which is also the place where its effect
  on the three projects is seen.
- A fourth repository of the corpus is one more directory in `tests/corpus/`.
