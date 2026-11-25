# raclab-dokime

*Leer en [español](README.es.md).*

A verification and evidence layer around coding agents. It does not write code: it helps a person
write a contract of requirements and approved examples, hands the work to an agent the user
already has, and accepts the result only through mechanical gates. What it delivers is a change
with signed evidence of what was checked, what was not, and who decided what. No result is taken
as good on the word of the agent that produced it.

## Status

Under construction, at version **0.2.0**. The reference architecture is written and its decisions
are accepted. Of the seven blocks of construction of phase 2, two are closed: **A** (audit) and
**B** (hold out). Block C, where the harness launches the agent, has not opened. The phases, the
blocks and their exit criteria are in [docs/ROADMAP.md](docs/ROADMAP.md).

It verifies Python projects only, observes them in containers with podman only, and reaches the
code at two boundaries: a function called with JSON values, and a command line.

### The commands that exist

| Command | What it does | What it checks |
|---|---|---|
| `dokime contract check` | Validates a contract file and says what it lacks | The format, the EARS text of each requirement, an example for each requirement, duplicates and contradictions. It runs nothing |
| `dokime contract seal` | Splits an approved contract and seals its held-out examples for the recipients of `.dokime/recipients.txt` | That the contract written keeps visible exactly the examples of the split, and that no held-out example is written into the project |
| `dokime env check` | Self-checks the pack of a project on its history | That the image of the pack builds, and that two commits of the history have tests that go from red to green in it |
| `dokime audit` | Audits a change that arrives already made, a patch on a base commit, against its contract, and writes the ledger of the run and an evidence file | The gates `contract`, `environment`, `baseline`, `protected-paths`, `existing-tests`, `visible-examples`, `repeatability`, `relations`, and `sealed-examples` where the key is |

Each command writes one line per finding and exits with a code for each verdict. How each one is
used is in the README of [`interfaces`](src/dokime/interfaces/README.md).

### What it has measured

On a corpus of cases on three public projects, with known verdicts: no false accept on patches
that fail visible examples, edit tests or break existing tests (block A), nor on the four cheating
techniques of the roadmap (block B). The bad cases were written by the session that builds, not by
an agent trying to cheat. The numbers and their limits are in the closing notes of
[block A](docs/ROADMAP.md#block-a--closing-note) and
[block B](docs/ROADMAP.md#block-b--closing-note).

### What it does not do yet

- **It does not launch an agent.** The change arrives already made, written by anyone; the loop
  that hands the task to an agent comes with block C.
- **It does not look at damage outside the change.** The gates `changed-line-coverage` and
  `behaviour-differences` appear in the evidence as not applicable, built in block D.
- **The evidence is not signed.** It is an unsigned statement; signing it, and verifying it
  without the harness, come with block E.
- **It does not help to write the contract.** A person writes it by hand; help comes with block F.
- **The gate of the sealed examples does not run in CI**
  ([ADR-0082](docs/adr/0082-the-sealed-gate-does-not-run-in-ci-in-block-b.md)): it runs only where
  the key is, by hand.
- **Of the relations, only `idempotent` at the command line** has been measured, in one case.

## Where things are

| What | Where |
|---|---|
| How we work: branches, commits, gates, definition of done | [CONTRIBUTING.md](CONTRIBUTING.md) |
| What the product is, its invariants and its modules | [docs/architecture/](docs/architecture/README.md) |
| Design and process decisions | [docs/adr/](docs/adr/README.md) |
| EARS requirements of each scope | [docs/requirements/](docs/requirements/) |
| Phases and exit criteria | [docs/ROADMAP.md](docs/ROADMAP.md) |

## Development

Requires [uv](https://docs.astral.sh/uv/).

```bash
uv sync --locked
uv run pytest
```

The gates CI runs are listed in [CONTRIBUTING.md](CONTRIBUTING.md#quality-gates).
