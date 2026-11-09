<!-- translation-of: 0003-rules-enforced-in-ci.md sha256:41278f34ee930e87 -->
# ADR-0003 · Las reglas se verifican en CI; las skills solo guían

**Estado:** aceptada

## Contexto

`dokime` tenía un plan con criterios de salida por fase y puntos de parada explícitos. Se saltaron:
unas 38 semanas de plan se ejecutaron en 16 días, con los benchmarks que debían frenar el avance
diferidos. Las reglas estaban escritas, pero nada impedía saltárselas.

Las skills de desarrollo (`.claude/skills/`) describen cómo trabajar, pero son instrucciones: un día
en que se va deprisa, se pueden ignorar.

## Decisión

Toda regla de proceso que se pueda comprobar de forma mecánica tiene una puerta en CI, y `main`
solo acepta cambios que pasan todas. Las skills guían cómo llegar a pasar esas puertas; nunca son
la única garantía de una regla.

## Alternativas descartadas

- **Reglas solo en documentación y skills.** Es lo que falló en `dokime`.
- **Adoptar una metodología externa completa** (por ejemplo, la biblioteca de skills Superpowers).
  Traería un segundo proceso, con su propio formato de planes y su uso de subagentes en paralelo,
  que es justo el tipo de aceleración que se quiere evitar. En su lugar se reutilizan y adaptan las
  skills de metodología de `dokime`.

## Consecuencias

- Las reglas que no se pueden comprobar (si un requisito expresa la intención correcta, si una
  decisión es buena) quedan para la revisión humana del PR, que es la puerta de decisión.
- Añadir una regla de proceso implica escribir su check, sus requisitos y sus tests.
