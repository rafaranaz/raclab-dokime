# ADR-0016 · Verification runs in a container without network, on the base commit plus the patch

**Status:** accepted

## Context

If the change is verified in the environment where the agent worked, anything the agent left
there (an installed package, a cached file, a modified test runner) can make the checks pass.

## Decision

- Verification starts from the base commit, applies the patch computed by the harness and runs in
  a container **without network**. A container engine is a requirement of the product.
- Three phases with different network: *prepare* reaches only the allowed package registries;
  *work* is the agent's; *verify* reaches nothing.
- Credentials for private registries are added from outside by a proxy. They never enter the image.
- A new dependency is not installed during the work. The agent requests it; the harness shows that
  the package exists in an allowed registry, its age and the change to the lock file; a person
  approves; the prepare phase runs again.
- Protected paths include the tests, their configuration and the harness directory. A change to
  them is dropped from the patch unless the contract authorises it, and the attempt goes on.
- Services the tests need run next to the code inside the isolated network and are reset before
  each verification. Tests that need an external network are excluded and declared.
- Every run starts from the image: nothing a run writes survives it, except the observations and
  result files it returns. The runtime records what it mounted and passed into the verification
  zone.

## Basis

Reasoning and documented practice. Automatic environment setup succeeds between 17 % and 38 % of
the time and 12.7 % of the results are false passes
([Multi-Docker-Eval](https://arxiv.org/abs/2512.06915)), which is why the baseline in
[ADR-0017](0017-damage-outside-the-change-against-a-baseline.md) is mandatory.

## Alternatives considered

- **Verify with a lightweight wrapper on the user's machine.** No clean environment, and the code
  under test shares the host.
- **Prepare without credentials.** Teams install from private registries.

## Consequences

- Docker, Podman or similar must be installed where verification runs. A team can verify only in
  CI and need nothing locally.
- Tests are run twice: by the agent while it works, and here.
