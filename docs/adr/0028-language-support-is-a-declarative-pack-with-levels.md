# ADR-0028 · Language support is a declarative pack with support levels

**Status:** accepted

## Context

The kernel must not know languages. Setting up the environment of an arbitrary repository
automatically works between 17 % and 38 % of the time, and 12.7 % of the results pass without
really testing anything.

## Decision

- A pack is data: how to recognise the project, its environment, the commands to build, test and
  measure coverage, how to serve it, its probe, its protected paths and its companion services.
- The environment comes from what the project already has: a Dockerfile, a devcontainer or its CI
  configuration. A pack proposed from them is verified before it is accepted.
- Three levels, recorded in the evidence:

  | Level | Requires | Enables |
  |---|---|---|
  | P1 | Environment, build, tests with a standard report | Regression audit |
  | P2 | An executable or a service | Examples at the `cli` and `http` boundaries |
  | P3 | A probe and coverage | The `function` boundary, changed-line coverage, impact map |

- The pack checks itself with the history of the project: a commit that added a test with a fix
  must have that test failing on the parent commit and passing on the fix.

## Basis

Literature and one partial test of our own.
[Multi-Docker-Eval](https://arxiv.org/abs/2512.06915) for the difficulty. Our test took the
commands from the CI of ten public repositories: five of the six that could be measured worked;
it has to be repeated with containers and registry access before it counts.

## Alternatives considered

- **Language code in several modules.** Every new language would touch the kernel.
- **Checking the pack by breaking a source file.** The linter or the compiler fails first, which
  does not show that the tests exercise the code.

## Consequences

- P1 and P2 need nothing written per language, which makes "any language" credible early.
- A project without a commit of that shape has a pack that is not self-checked, and it is noted.
