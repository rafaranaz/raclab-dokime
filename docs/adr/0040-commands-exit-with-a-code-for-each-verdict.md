# ADR-0040 · Commands exit with a code for each verdict

**Status:** accepted

## Context

Milestone A1 delivers the first command, `contract check`. A command is used by a person at a
terminal and by scripts and pipelines, which read its exit code and sometimes its output. The
harness has four verdicts ([ADR-0015](0015-a-gate-returns-one-of-four-verdicts.md)), and the
common convention for exit codes has room for three states.

## Decision

- **Exit codes.** A command exits with the code of the verdict it reached:

| Verdict | Code |
|---|---|
| `PASS` | 0 |
| `FAIL` | 1 |
| `ERROR`, and a command line that is not valid | 2 |
| `ASK` | 3 |

- **Text output.** Findings go to the standard output, one per line, as
  `path:line: VERDICT code: message`, and a last line gives the verdict and the counts. How the
  command is used, when the command line is not valid, goes to the standard error.
- **Output for programs.** `--format json` writes one JSON document with the file, the verdict and
  the findings. Other formats are added when something needs them.
- **Language.** The output of the commands is in English. It is an interface for tools and for
  the person who runs them; the interaction in the person's language of
  [ADR-0032](0032-bilingual-interaction-signs-what-was-shown.md) is about what a person approves.
- **Library.** The command line is parsed with `argparse`, from the standard library.

## Basis

Verified by running the tools:

| Tool | Clean | Findings | Could not work | Other states |
|---|---|---|---|---|
| `grep`, `diff` | 0 | 1 | 2 | — |
| ruff | 0 | 1 | 2 for an invalid option | — |
| mypy | 0 | 1 | 2 for an invalid option | — |
| pytest | 0 | 1 | 2 to 4 | 5 when no test was collected, 6 |
| `argparse`, on a usage error | — | — | 2 | — |

ruff and mypy write their findings to the standard output, one per line, as
`file:line: code message`. ruff offers twelve output formats, among them `json`, `github` and
`sarif`.

Read in the sources: the manual of `gh` documents 0, 1, 2 for a cancelled command and 4 when the
command requires authentication, a state that asks something of a person and has a code of its
own. GitHub Actions turns a line `::error file=…,line=…::message` into an annotation.

So the convention is 0 clean, 1 findings, 2 could not work, and a tool with a state outside those
three gives it its own code. `ASK` is such a state. Reasoning, without a test: that a pipeline
which looks only at the exit code should not let a question pass unseen. Not looked at: SARIF.

## Alternatives considered

- **`ASK` exits with 0, and an option makes it fail.** A pipeline that does not know the option
  passes questions in silence.
- **`ASK` exits with 1.** A script cannot tell "fix the contract" from "answer a question".
- **click or typer.** More comfortable subcommands, for one more dependency to audit.
- **The GitHub or SARIF formats now.** Nothing uses them until the audit runs in CI, in
  milestone A4.

## Consequences

- A script can branch on the four verdicts without reading the output.
- An error of the command line and a verdict `ERROR` share the code 2: in both the tool could not
  evaluate.
- Every later command (`audit`, `evidence verify`) follows the same codes and the same line
  format.
