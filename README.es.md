<!-- translation-of: README.md sha256:295d56e12db37b10 -->
# raclab-dokime

*Read in [English](README.md).*

Una capa de verificación y evidencia alrededor de los agentes de programación. No escribe código:
ayuda a una persona a escribir un contrato de requisitos y ejemplos aprobados, entrega el trabajo a
un agente que el usuario ya tiene, y acepta el resultado solo a través de puertas mecánicas. Lo que
entrega es un cambio con evidencia firmada de qué se comprobó, qué no, y quién decidió qué. Ningún
resultado se da por bueno por la palabra del agente que lo produjo.

## Estado

En construcción. La arquitectura de referencia está escrita y sus decisiones están aceptadas. El
repositorio está en la **fase 2, bloque A** (auditar), y todavía no contiene código del harness. Las fases, los
bloques de construcción y sus criterios de salida están en [docs/ROADMAP.es.md](docs/ROADMAP.es.md).

## Dónde está cada cosa

| Qué | Dónde |
|---|---|
| Cómo se trabaja: ramas, commits, puertas, definición de terminado | [CONTRIBUTING.es.md](CONTRIBUTING.es.md) |
| Qué es el producto, sus invariantes y sus módulos | [docs/architecture/](docs/architecture/README.es.md) |
| Decisiones de diseño y de proceso | [docs/adr/](docs/adr/README.es.md) |
| Requisitos EARS de cada ámbito | [docs/requirements/](docs/requirements/) |
| Fases y criterios de salida | [docs/ROADMAP.es.md](docs/ROADMAP.es.md) |

## Desarrollo

Requiere [uv](https://docs.astral.sh/uv/).

```bash
uv sync --locked
uv run pytest
```

Las puertas que ejecuta CI están en [CONTRIBUTING.es.md](CONTRIBUTING.es.md#puertas-de-calidad).
