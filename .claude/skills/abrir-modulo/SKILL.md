---
name: abrir-modulo
description: Abrir el trabajo de un ámbito nuevo (un módulo del harness o una pieza de gobierno). Usar antes de escribir cualquier código de ese ámbito.
---

# Abrir un ámbito

## Antes de empezar

1. **Comprueba que no hay otro módulo abierto.** Solo hay uno a la vez
   ([docs/ROADMAP.md](../../../docs/ROADMAP.md)). Si lo hay, para y pregunta.
2. **Comprueba que la fase lo permite.** Si el ámbito no está en la fase actual de la hoja de ruta,
   para y pregunta.
3. **Lee la arquitectura del módulo** en `docs/architecture/`, cuando exista: su interfaz, sus
   dependencias permitidas y su puerta de cierre.

## Pasos

1. **Crea la rama** desde `main` actualizada: `tipo/ámbito-descripción`
   (por ejemplo `feat/core-config-loading`).
2. **Declara el ámbito** en `tools/scopes.toml` con sus rutas: `src/dokime/<ámbito>/**`,
   `tests/<ámbito>/**` y `docs/requirements/<ámbito>.md`. Es el primer commit de la rama.
3. **Escribe los requisitos** en `docs/requirements/<ámbito>.md` con la skill `requisitos-ears`, y
   pásalos por `uv run python -m tools.check_ears`.
4. **Abre el PR como borrador** con los requisitos, antes de escribir código. Revisar los
   requisitos es mucho más barato que revisar código construido sobre requisitos equivocados.
5. **Construye requisito a requisito** con la skill `tdd`.

## Durante el trabajo

- **No toques nada fuera de las rutas del ámbito.** Si hace falta, es otra rama. `check_scope` lo
  rechaza igualmente.
- **Si el alcance cambia** (un requisito nuevo que no estaba previsto, una dependencia que la
  arquitectura no permite, un problema en otro módulo), para y pregunta. No lo resuelvas en
  silencio.
- **Commits pequeños**, cada uno con su porqué y todas las puertas en verde.
