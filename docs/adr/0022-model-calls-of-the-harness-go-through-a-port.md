# ADR-0022 · The model calls of the harness go through a port with three routes

**Status:** accepted

## Context

The harness needs a model for the interview, for proposing examples and for formalising
requirements. Calling through the installed agent asks nothing more of the user, but it leaves
what was generated in the history of that agent, which the same agent can read when it implements.
The MCP feature that lets a server ask the client's model is deprecated.

## Decision

- A port with three adapters: an OpenAI-compatible API (which includes local servers), a vendor
  API, and the installed agent. None is the default; the configuration chooses, per task if wanted.
- **Held-out content never goes through the installation of the agent that implements**, and
  neither do the examples of a contract before the split: the installed-agent adapter is not used
  to propose or handle examples of a contract that agent will implement.
- Every prompt is a registered template with an identifier and a digest. Every answer is validated
  against a schema, retried once, and otherwise is an error.
- Everything a model returns has origin `model` ([ADR-0013](0013-provenance-decides-what-a-check-can-do.md)).

## Basis

Literature and reasoning. The MCP specification of 2026-07-28 deprecates sampling and recommends
integrating directly with provider APIs
([changelog](https://modelcontextprotocol.io/specification/2026-07-28/changelog.md)). Open-weight
models stop calling tools when tools and a JSON schema are both active
([study](https://www.alphaxiv.org/abs/2606.25605.md)), so structured calls carry no tools.

## Alternatives considered

- **Always through the installed agent.** No key needed; less control of the format and the leak
  described in the context.
- **Always a direct API.** It demands a key or a local model from a user who has a subscription.

## Consequences

- Three adapters to maintain.
- A user without a key can run everything except the proposal of examples locally, unless
  a local model is configured.
