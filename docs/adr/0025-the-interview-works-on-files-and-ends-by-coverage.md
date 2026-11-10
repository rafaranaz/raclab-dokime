# ADR-0025 · The interview works on files and ends by coverage

**Status:** proposed

## Context

Models rarely ask before coding, and when they interview they stop early: they use four to eight
rounds out of twenty and discover a small share of the implicit requirements. Asking helps, and an
interviewer guided by a structure of categories discovers far more.

## Decision

- The interview is between the harness and the person. The coding agent takes no part.
- It works on the contract files. The model proposes examples with their input and output; the
  person approves or corrects them. Each answer is written at once, with who answered, and the
  changed fragment is shown for confirmation.
- One question at a time, with options, a recommended one, and always a bounded text answer with
  fixed fields.
- **The harness decides when it ends, by coverage of categories.** There is no cap by default.
  When the person says enough, what is left becomes one list of assumptions to approve, with the
  answer a model suggests marked as delegated.
- Doubts are classified with a bias towards asking. A person may delegate answers to interview
  questions to a model; the delegation is recorded and never covers the approval of an example or
  of the contract, nor a question raised by a gate.
- A question is data, with the restrictions of MCP forms. Surfaces: files and the terminal; MCP
  forms when the harness is entered from an editor, for clarifying questions only; a mode without
  questions for CI.
- Examples and the contract are approved in a channel where the harness talks to the person
  directly: files or the terminal. An answer that arrives through an MCP form is recorded as
  coming through the client, unverified, because the client can read the form and answer in the
  person's place.

## Basis

Literature. Asking raises correctness from 71 % to 81 % with people
([ClarifyGPT](https://arxiv.org/abs/2310.10996)); unguided models discover at most a third of the
implicit requirements ([ReqElicitGym](https://arxiv.org/abs/2602.18306); its published data and
its paper differ); a guided interviewer reaches 0.69 on the same benchmark
([study](https://arxiv.org/abs/2605.05828)). Interviewing over the file, updating it after each
answer, is what Spec Kit's `clarify` does, with a cap of five questions.

A test of ours, with one agent run headless: the model saw neither an MCP form nor its answer, and
nothing was left in the session files, but a hook of the client received the form and answered it.
The [specification](https://modelcontextprotocol.io/specification/latest/client/elicitation) says
that in form mode the data is exposed to the client.

## Alternatives considered

- **A cap of a few questions.** The useful questions come late.
- **Approving a finished document at the end.** Colder, and easier to approve without reading.

## Consequences

- No evidence was found on whether people approve examples with attention; a test plants a wrong
  example, announced in the policy, and counts.
- Questions that need something visual do not fit a terminal.
