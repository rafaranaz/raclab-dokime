<!-- translation-of: 0003-rules-enforced-in-ci.md sha256:dffee51f7303ff6e -->
# ADR-0003 · Las reglas se verifican en CI; las skills solo guían

**Estado:** aceptada

## Contexto

Un plan con criterios de salida por fase y puntos de parada explícitos no se sostiene por estar
escrito. Cuando se va deprisa los puntos de parada se saltan y las mediciones que debían frenar el
avance se difieren, porque nada lo impide.

Las skills de desarrollo (`.claude/skills/`) describen cómo trabajar, pero son instrucciones: un día
en que se va deprisa, se pueden ignorar.

## Decisión

Toda regla de proceso que se pueda comprobar de forma mecánica tiene una puerta en CI, y `main`
solo acepta cambios que pasan todas. Las skills guían cómo llegar a pasar esas puertas; nunca son
la única garantía de una regla.

## Alternativas descartadas

- **Reglas solo en documentación y skills.** Nada impide saltárselas bajo presión.
- **Adoptar una metodología externa completa** (por ejemplo, la biblioteca de skills Superpowers).
  Traería un segundo proceso, con su propio formato de planes y su uso de subagentes en paralelo,
  que es justo el tipo de aceleración que se quiere evitar. En su lugar el repositorio mantiene
  unas pocas skills propias y breves.

## Consecuencias

- Las reglas que no se pueden comprobar (si un requisito expresa la intención correcta, si una
  decisión es buena) quedan para la revisión humana del PR, que es la puerta de decisión.
- Añadir una regla de proceso implica escribir su check, sus requisitos y sus tests.
