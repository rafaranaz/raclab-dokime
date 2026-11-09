# Cómo se trabaja en raclab-dokime

El harness se basa en un principio: **cada paso lo propone alguien (un agente o una persona) y lo
acepta o rechaza una verificación mecánica**. Este repositorio aplica ese mismo principio a su
propio desarrollo. Las reglas de este documento no dependen de la buena voluntad: cada una tiene
una puerta en CI que la comprueba.

| Principio del harness | Cómo se aplica aquí |
|---|---|
| Decisión + verificación mecánica | Todo entra por PR; se mergea solo con CI en verde y aprobación humana |
| Contrato EARS | Cada ámbito tiene sus requisitos en `docs/requirements/<ámbito>.md` antes del código |
| Trazabilidad requisito ↔ test | Cada fichero de test declara qué requisitos prueba; CI falla si alguno queda sin test |
| Radio de impacto acotado | Cada rama declara un ámbito y CI rechaza cambios fuera de sus rutas |
| Registro de decisiones | ADR en `docs/adr/`; la historia vive en git, no en el código |
| Criterios de salida | Cada fase de [docs/ROADMAP.md](docs/ROADMAP.md) tiene los suyos; la siguiente no se abre sin cumplirlos |

## Ciclo de un ámbito

Un ámbito es un módulo del harness (`core`, `graph`, `spec`...) o una pieza de gobierno (`repo`,
`arch`). Su lista cerrada está en [tools/scopes.toml](tools/scopes.toml), con las rutas que le
pertenecen.

1. **Abrir.** Se declara el ámbito en `tools/scopes.toml`, se crea la rama y se escriben los
   requisitos EARS. Ver la skill [abrir-modulo](.claude/skills/abrir-modulo/SKILL.md).
2. **Construir con TDD.** Cada requisito pasa por un test en rojo demostrado antes de la
   implementación. Ver la skill [tdd](.claude/skills/tdd/SKILL.md).
3. **Cerrar.** Se ejecutan todas las puertas en local, se redacta el informe de cierre y se abre o
   actualiza el PR. Ver la skill [cerrar-modulo](.claude/skills/cerrar-modulo/SKILL.md).

**Solo hay un ámbito de módulo abierto a la vez.** El siguiente no se abre hasta que el anterior
está mergeado.

## Ramas

- `main` está protegida: sin push directo, solo merge por PR con CI en verde.
- Formato: `tipo/ámbito-descripción`, en minúsculas y con guiones. Por ejemplo
  `feat/graph-ambiguity-confidence` o `docs/arch-c4-context`.
- `tipo` es un tipo de Conventional Commits y `ámbito` uno de `tools/scopes.toml`. Los ámbitos no
  llevan guiones, porque el primer guion separa el ámbito de la descripción.
- Las ramas viven poco: si una rama crece más de lo que se puede revisar de una sentada, se parte.
- El merge es **por rebase**: el historial de `main` es lineal y cada commit se conserva.

## Commits

Formato [Conventional Commits](https://www.conventionalcommits.org/), en inglés:

```
type(scope): imperative description in lower case

Body explaining WHY the change is needed: the problem, the constraint or
the decision behind it. What changed is already in the diff.

Optional-Trailer: value
```

- `type`: `build`, `chore`, `ci`, `docs`, `feat`, `fix`, `perf`, `refactor`, `revert`, `style`, `test`.
- `scope` es obligatorio y debe ser el ámbito de la rama.
- La cabecera tiene como máximo 72 caracteres.
- `feat`, `fix`, `refactor` y `perf` necesitan cuerpo. Los trailers (`Co-Authored-By:`...) no
  cuentan como cuerpo.
- Un commit es una unidad de cambio lógica y autocontenida, no el volcado de una sesión.
- No hay commits de merge en las ramas: se rebasan sobre `main`.

## Pull requests

- Pequeños y revisables de una sentada. La plantilla pide el ámbito, los requisitos afectados y las
  puertas.
- La aprobación humana es la puerta de decisión: CI dice si el cambio es correcto según las
  reglas; la revisión dice si es el cambio que queremos.
- Nunca se mergea con CI en rojo ni con un hallazgo de revisión abierto.

## Puertas de calidad

Todas se ejecutan en CI ([.github/workflows/ci.yml](.github/workflows/ci.yml)) y se pueden ejecutar
en local con los mismos comandos.

| Puerta | Comando | Umbral |
|---|---|---|
| Lint, incluida seguridad (`S`) y complejidad ciclomática | `uv run ruff check .` | Sin hallazgos; complejidad ≤ 10 por función |
| Formato | `uv run ruff format --check .` | Sin diferencias |
| Tipos | `uv run mypy` | Modo estricto, sin errores |
| Tests y cobertura | `uv run pytest --cov` | Todos en verde; cobertura de ramas ≥ 90 % |
| Historia en el código | `uv run python -m tools.check_history` | Sin hallazgos |
| Sintaxis EARS | `uv run python -m tools.check_ears` | Sin hallazgos |
| Trazabilidad | `uv run python -m tools.check_traceability` | Todo requisito con test; todo test con marcador |
| Enlaces en Markdown | `uv run python -m tools.check_links` | Sin enlaces rotos |
| Ficheros versionados e ignorados | `git ls-files --cached --ignored --exclude-standard` | Salida vacía |
| Commits | `uv run python -m tools.check_commits --base origin/main --branch <rama>` | Sin hallazgos |
| Ámbito de la rama | `uv run python -m tools.check_scope --base origin/main --branch <rama>` | Sin hallazgos |
| Dependencias | `pip-audit` sobre las dependencias del lockfile | Sin vulnerabilidades conocidas |

Las fronteras entre módulos (contratos de importación) y la validación de diagramas Mermaid se
añaden en la Fase 1, cuando exista la arquitectura que las define.

## Requisitos y trazabilidad

Cada ámbito tiene un fichero `docs/requirements/<ámbito>.md`. Cada requisito ocupa una línea:

```
- **CORE-001** When a gate rejects an attempt, the runner shall route to the state named by the gate.
```

- El identificador es el nombre del fichero en mayúsculas, un guion y tres dígitos.
- La frase sigue una de las cinco plantillas EARS, contiene un solo `shall` y no usa términos
  vagos. La skill [requisitos-ears](.claude/skills/requisitos-ears/SKILL.md) explica cómo
  escribirlos.
- Cada fichero de test declara en su primera línea no vacía qué requisitos prueba:

  ```python
  # SDD-EARS: CORE-001 CORE-002
  ```

## Comentarios y documentación

- **El código explica qué hace y por qué, no cómo se llegó ahí.** Nada de identificadores de tarea,
  versiones, fechas ni relatos de incidentes en comentarios o docstrings: eso está en git y en los
  ADR. `tools/check_history.py` lo rechaza.
- Un comentario que no aporta nada que el código no diga ya, sobra.
- Toda referencia a un documento debe apuntar a un fichero que existe en el repositorio.
- Idiomas: la documentación va en español; el código, los identificadores, los comentarios, los
  mensajes de commit y los requisitos EARS van en inglés ([ADR-0005](docs/adr/0005-idiomas.md)).

## Definición de terminado de un ámbito

- Requisitos EARS escritos y revisados.
- Cada requisito con al menos un test, rojo demostrado antes de su implementación.
- Interfaz pública documentada en un README breve del módulo: qué hace y cómo se usa.
- Todas las puertas en verde, en local y en CI.
- ADR para cada decisión con consecuencias.
- Informe de cierre en la descripción del PR.
- Criterios de salida de la fase actualizados en [docs/ROADMAP.md](docs/ROADMAP.md).
