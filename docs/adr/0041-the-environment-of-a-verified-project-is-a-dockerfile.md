# ADR-0041 · The environment of a verified project is a Dockerfile, and its pack proves itself

**Status:** accepted, amended by [ADR-0042](0042-memory-persists-on-local-disk-or-in-its-own-git-repository.md)

## Context

Milestone A2 builds the environment of a verified project from its pack and checks that the pack
can be trusted. [ADR-0028](0028-language-support-is-a-declarative-pack-with-levels.md) says what a
pack is and [ADR-0016](0016-verification-in-a-container-on-base-plus-patch.md) how verification
runs. They leave open how the environment is written down, who writes it, how the commits of the
self-check are chosen, which tool builds and runs, and what is enforced in the first version.

## Decision

- **A Dockerfile.** The pack names a Dockerfile, the one of the project or one written beside the
  pack. It is the only way to describe an environment in the first version.
- **Nobody guesses it.** The harness does not derive a pack from a repository. A person writes it,
  using what the project has: its Dockerfile if it works, or the commands of its pipeline.
- **The self-check finds its own witnesses.** The harness takes the latest commits of the project
  that change a test and code that is not a test. For each, it runs the tests of that commit on
  its parent and on the commit itself. A commit is a witness when a test fails on the parent and
  passes on the commit. The pack passes with two witnesses among the first ten candidates, and the
  witnesses are recorded so that the next run uses the same ones.
- **Network.** Verification runs without network; an engine that cannot do that is not used.
  Preparation uses the network without restriction in this version, and the result says so as
  not checked. The restriction to allowed registries of ADR-0016 is decided before block C.
- **The base image is recorded, not pinned.** A Dockerfile may start from a moving tag. The
  harness records the digest of the image it built and of the base that the tag resolved to.
- **Building and running are two commands.** Each is configured apart, among `docker`, `podman`
  and `buildah`. An adapter declares what it guarantees besides the absence of network: limits of
  memory, processor and processes, and a read-only root. What the chosen engine does not guarantee
  is recorded as not checked.
- **Scope of A2.** Level P1: environment, build and tests with a report in JUnit XML. The pack is
  `.dokime/pack.yaml` in the project, or a file given to the command.

## Basis

Read in the sources:

- Deriving the environment of an unknown repository fails often. In [EnvBench](https://arxiv.org/html/2503.14443) (994 repositories) a
  fixed script configures 15.9% of the Python projects, and on the rest the best agent reaches
  6.7% for Python and 29.5% for the JVM. [Repo2Run](https://arxiv.org/abs/2502.13681) reports 86% of 420 Python repositories, counting
  as success that the tests can be run, whether they pass or not.
- SWE-bench does not derive it: the installation and the tests are declared per repository and
  version, and each case is validated by the tests that go from failing to passing.
- `devcontainer.json` defines its environment as an image, a Dockerfile it points to or a Compose
  file: it wraps a Dockerfile, it does not replace it. Cloud Native Buildpacks build an image
  with no configuration file by detecting the language, which is the path this decision avoids.
- Of 2,000 repositories with a Dockerfile, 56.1% built and 2.7% gave the same image bit for bit
  ([study](https://arxiv.org/html/2602.17678v1)). So the Dockerfile a project has may not work,
  which the self-check catches, and identical images are not promised.
- The manual of `buildah run` has `--network none`, `--cap-drop`, read-only mounts and rootless
  isolation, and lists no limit of memory, processor or processes and no read-only root.

Verified on the clones: none of the three repositories of the corpus has a Dockerfile or a
devcontainer; the three have a workflow, and two use tox.

From memory, not checked: that the format of images is the standard of OCI while the Dockerfile
is a format by use, and that `podman` has the limits that `buildah run` lacks. Reasoning, without
a test: that the Dockerfile a project has is often meant to deploy it and not to run its tests;
the numbers two and ten of the self-check. Not run: any of the engines, which this session does
not have. Not looked at: Nix.

## Alternatives considered

- **The pack holds a base image and a list of commands, and the harness writes the Dockerfile.**
  One more format to learn, for what a Dockerfile already says.
- **Accept `devcontainer.json` now.** It adds its command-line tool as a dependency, and it ends
  in a Dockerfile anyway. It can be added later at a low cost.
- **A tool that proposes the pack from the pipeline of the project.** The hypothesis of the
  roadmap is tested by hand first, on the three repositories of the corpus.
- **A person lists the commits of the self-check.** More work for each pack, and the person
  chooses what proves them right.
- **Build the proxy that restricts the registries now.** No agent is in the circuit until
  block C.
- **Require the base image pinned by its digest.** Stricter, and it does not give identical
  images either.

## Consequences

- A project without a Dockerfile that works costs one to adopt, written by a person.
- The same pack can give different guarantees on different engines, and the evidence says which.
- A project with fewer than two commits that fix a defect with a test cannot pass the self-check.
