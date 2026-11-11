# raclab-dokime

*Leer en [español](README.es.md).*

A verification and evidence layer around coding agents. It does not write code: it helps a person
write a contract of requirements and approved examples, hands the work to an agent the user
already has, and accepts the result only through mechanical gates. What it delivers is a change
with signed evidence of what was checked, what was not, and who decided what. No result is taken
as good on the word of the agent that produced it.

## Status

Under construction. The reference architecture is written and its decisions are accepted. The
repository is in **phase 2, block A** (audit), and it does not contain any harness code yet. The phases,
the blocks of construction and their exit criteria are in [docs/ROADMAP.md](docs/ROADMAP.md).

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
