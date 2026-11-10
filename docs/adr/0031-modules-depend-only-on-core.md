# ADR-0031 · Modules depend only on core; adapters are imported only by the composition root

**Status:** proposed

## Context

Modules are built one at a time, so each has to be buildable and testable without the others.
Cyclic dependencies precede other architecture problems in 60 % to 80 % of the cases studied.

## Decision

- `core` imports no other module. It holds the types, the verdicts, the ledger and the ports.
- Domain modules (`contract`, `oracle`, `evidence`, `packs`) import only `core`; `oracle` also
  imports `contract`. Domain services (`spec`, `verify`, `delivery`) import those and do not
  import each other. `engine` imports the services.
- Adapters (`sandbox`, `agents`, `gateway`) import only `core` and implement its ports. Only
  `interfaces`, the composition root, imports adapters.
- `evidence` imports nothing but `core`, so that verifying evidence can be installed with those
  two modules alone.
- Every port has at least two adapters foreseen from the start, and takes the shape of an existing
  standard where one exists.
- These rules are import contracts checked in CI.

## Basis

Literature and practice. [Architectural smells study](https://arxiv.org/abs/2203.08702), an
industrial case.

## Alternatives considered

- **A layered stack with the engine on top of everything.** The engine becomes the place where
  orchestration leaks into code.
- **Free imports without cycles.** Each module would need the others to be tested.

## Consequences

- More ports and more wiring in the composition root.
- A port with a single adapter is an assumption, and is treated as one.
