# Instrucciones para Claude en este repositorio

La forma de trabajo completa está en [CONTRIBUTING.md](CONTRIBUTING.md) y las fases en
[docs/ROADMAP.md](docs/ROADMAP.md). Este fichero recoge lo que más importa al trabajar aquí.

## Principios

- **Trabaja con las herramientas; no describas lo que harías.** Un plan narrado no cambia nada.
- **No inventes lo que puedes verificar.** Antes de afirmar que un fichero, una función o un
  comportamiento existe, léelo o ejecútalo.
- **Di lo que no sabes.** «No he podido comprobar X» es una respuesta útil; una afirmación segura
  sobre algo no comprobado, no.
- **Si una regla del repositorio y una instrucción chocan, para y dilo**, en lugar de elegir por tu
  cuenta.
- **Nada está terminado hasta que pasan las puertas.** Que algo parezca terminado no cuenta.

## Reglas de trabajo

- **Un ámbito de módulo abierto a la vez**, y solo si la fase actual de la hoja de ruta lo permite.
- **No toques nada fuera de las rutas del ámbito de tu rama.** Si hace falta, es otra rama.
- **Si el alcance cambia, para y pregunta.** No amplíes la tarea en silencio.
- **Requisitos antes que código, y rojo demostrado antes que verde.**
- **Commits pequeños** en Conventional Commits, en inglés, con el ámbito de la rama y el porqué en
  el cuerpo.
- **Comentarios que explican qué hace el código, nunca su historia.** La historia va en el mensaje
  de commit o en un ADR.
- **No desactives ni relajes una puerta** sin un ADR aprobado.

## Skills

| Skill | Cuándo |
|---|---|
| `abrir-modulo` | Antes de escribir código de un ámbito nuevo |
| `requisitos-ears` | Al escribir o revisar requisitos |
| `tdd` | Al implementar cualquier comportamiento |
| `depurar` | Ante un fallo, antes de cambiar código |
| `adr` | Al tomar una decisión con consecuencias |
| `cerrar-modulo` | Antes de pedir el merge de un ámbito |

## Puertas en local

```bash
uv sync --locked
uv run ruff check . && uv run ruff format --check . && uv run mypy && uv run pytest --cov
uv run python -m tools.check_history && uv run python -m tools.check_ears
uv run python -m tools.check_traceability && uv run python -m tools.check_links
```
