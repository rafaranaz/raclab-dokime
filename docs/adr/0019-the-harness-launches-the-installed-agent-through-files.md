# ADR-0019 · The harness launches the installed agent and talks to it through files

**Status:** proposed

## Context

Someone has to decide the order of the steps and record them. If the agent calls the harness when
it sees fit, the order depends on a model. Every agent has its own interface; files are the only
thing they all share.

## Decision

- The harness launches the agent the user already has, without its interface, with the user's
  installation, session and configuration.
- The task goes in as files: the requirements, the visible examples, the list of tests at risk,
  the result of the previous attempt, and a fixed template. The template tells the agent to stop
  and dispute when an example contradicts a requirement.
- The result is the state of the working tree. **The harness computes the patch** against the base
  commit; it does not rely on what the agent reports.
- The agent may leave signals as files (a dispute, a dependency request, notes), validated against
  a schema.
- The harness exposes no control interface on the network while the agent works.
- Launching is a port. The first adapter is each agent's own headless mode, described by a profile
  that is data and includes how the model is paid for. ACP is the second adapter.
- A change made by hand, or by an agent that cannot be launched, enters through audit mode.

## Basis

Literature and reasoning. Letting the model choose the next step costs between 2.5 and 17.5
points ([STAGE](https://arxiv.org/abs/2608.22538), one study). Prompt wording and a way out to ask
for help are what most reduce cheating ([ImpossibleBench](https://arxiv.org/abs/2510.20270)).
The control-interface rule comes from
[CVE-2026-82533](https://www.ox.security/blog/cve-2026-82533-deepseek-harness-ai-agent-sandbox-escape/).

## Alternatives considered

- **The agent calls the harness as a tool.** The order and the count of attempts would depend on
  the agent.
- **One adapter written in code per agent.** A profile as data makes a new agent a new file.

## Consequences

- Headless use of a subscription depends on a vendor policy that changed in 2026; the payment mode
  is recorded so that a change of policy is a change of one field.
- Agents that only live inside an editor can be audited but not launched.
