---
name: cerrar-modulo
description: Cerrar el trabajo de un ámbito antes de pedir su merge. Usar cuando se cree que el ámbito está terminado, para comprobarlo y redactar el informe de cierre.
---

# Cerrar un ámbito

Un ámbito no está terminado porque lo parezca, sino cuando pasa su definición de terminado
([CONTRIBUTING.md](../../../CONTRIBUTING.md#definición-de-terminado-de-un-ámbito)).

## 1. Ejecuta todas las puertas en local

```bash
uv sync --locked
uv run ruff check .
uv run ruff format --check .
uv run mypy
uv run pytest --cov
uv run python -m tools.check_history
uv run python -m tools.check_ears
uv run python -m tools.check_traceability
uv run python -m tools.check_links
git ls-files --cached --ignored --exclude-standard
uv run python -m tools.check_commits --base origin/main --branch "$(git branch --show-current)"
uv run python -m tools.check_scope --base origin/main --branch "$(git branch --show-current)"
```

Si alguna falla, el ámbito no está cerrado. Arréglalo con las skills `tdd` o `depurar`; no la
desactives ni bajes su umbral sin un ADR.

## 2. Comprueba lo que CI no puede comprobar

- ¿Cada requisito expresa la intención acordada, y no solo pasa el check de sintaxis?
- ¿Los tests prueban comportamiento y no detalles internos?
- ¿El README del módulo explica qué hace y cómo se usa, sin contar su historia?
- ¿Hubo decisiones con consecuencias? Cada una necesita su ADR.

## 3. Redacta el informe de cierre en la descripción del PR

- **Qué hace el módulo**, en dos o tres frases.
- **Requisitos**: cuántos, y la lista de identificadores.
- **Puertas**: resultado de cada una y cobertura del módulo.
- **Limitaciones conocidas**, dichas sin rodeos: lo que no hace o lo que no se ha podido comprobar.
- **ADR** nuevos o sustituidos.

## 4. Actualiza la hoja de ruta

Marca en `docs/ROADMAP.md` los criterios de salida cumplidos. El siguiente ámbito no se abre hasta
que este PR esté mergeado.
