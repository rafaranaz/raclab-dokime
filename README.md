# raclab-dokime

*Leer en [español](README.es.md).*

A spec-driven pipeline for coding agents: from a natural-language request to a published change,
where every step is proposed by an agent and accepted or rejected by a mechanical check. No result
is taken as good on the word of the agent that produced it.

## Status

Under construction. The repository is in **phase 0** (working agreement and quality gates); it does
not contain any harness code yet. The phases, their scope and their exit criteria are in
[docs/ROADMAP.md](docs/ROADMAP.md).

## Where things are

| What | Where |
|---|---|
| How we work: branches, commits, gates, definition of done | [CONTRIBUTING.md](CONTRIBUTING.md) |
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
