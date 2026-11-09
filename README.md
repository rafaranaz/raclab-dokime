# raclab-dokime

Pipeline de desarrollo guiado por especificación para agentes de código: de una petición en
lenguaje natural a un cambio publicado, donde cada paso lo propone un agente y lo acepta o
rechaza una verificación mecánica. Ningún resultado se da por bueno por la palabra del agente
que lo produjo.

## Estado

En construcción. El repositorio está en la **Fase 0** (forma de trabajo y puertas de calidad);
todavía no contiene código del harness. Las fases, su alcance y sus criterios de salida están en
[docs/ROADMAP.md](docs/ROADMAP.md).

## Dónde está cada cosa

| Qué | Dónde |
|---|---|
| Cómo se trabaja: ramas, commits, puertas, definición de terminado | [CONTRIBUTING.md](CONTRIBUTING.md) |
| Decisiones de diseño y de proceso | [docs/adr/](docs/adr/README.md) |
| Requisitos EARS de cada módulo | [docs/requirements/](docs/requirements/) |
| Fases y criterios de salida | [docs/ROADMAP.md](docs/ROADMAP.md) |

## Desarrollo

Requiere [uv](https://docs.astral.sh/uv/).

```bash
uv sync --locked
uv run pytest
```

Las mismas puertas que ejecuta CI se describen en
[CONTRIBUTING.md](CONTRIBUTING.md#puertas-de-calidad).
