# ADR-0020 · Isolating the agent is optional; adoption climbs a ladder

**Status:** proposed

## Context

Developers already use their agent on their own machine. Forcing a container or a wrapper changes
how they work and breaks agents that need their tools and their network. The guarantees of the
product do not come from where the agent ran.

## Decision

| Step | What changes for the developer | What is obtained |
|---|---|---|
| 0 · Audit in CI | Nothing | Full verification and evidence on the pull request |
| 1 · Audit locally | One command before pushing; a container engine | The same before pushing |
| 2 · The harness launches the agent | One command instead of opening the agent | The retry loop with feedback |
| 3 · With a wrapper | The agent may lose tools that need the network | Protection of the machine and its credentials |

- The wrapper is off unless the user or the policy asks for it. A working copy is also optional:
  the agent may work in the user's repository on a branch, from a clean tree.
- **The key of the sealed examples lives only in CI.** A developer's machine cannot decrypt them,
  so their secrecy does not depend on local isolation. A single developer without CI keeps the key
  locally, and the evidence states it as best effort.
- When the wrapper is on, it denies the local network towards the harness, and it is probed before
  each launch.
- The evidence records the step and whether a wrapper was used.

## Basis

Reasoning. Agents in permissive frameworks act outside the request between 5.4 % and 27.7 % of
the time ([study](https://arxiv.org/abs/2605.18583)), which is the risk the wrapper addresses and
the user already carries today.

## Alternatives considered

- **Wrapper on by default.** It protects the machine, but it is the whole friction and the oracle
  does not need it.
- **A mandatory container for the agent.** Every agent would have to be supported inside it.

## Consequences

- Without a wrapper, an agent can still damage files or read credentials on the user's machine.
- Sealed results arrive when the change is pushed, not before.
