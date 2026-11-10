<!-- translation-of: 0002-new-repository-ported-by-module.md sha256:c9bfb5d63b0234fd -->
# ADR-0002 · Repositorio nuevo, portado módulo a módulo

**Estado:** sustituida por el [ADR-0008](0008-built-new-nothing-is-ported.es.md)

## Contexto

Existía una implementación anterior del arnés. Sus paquetes dependían unos de otros en ciclos, de
modo que cualquier limpieza en sitio obligaba a tocar casi todo a la vez.

## Decisión

Este repositorio se crea vacío, con sus fronteras y sus puertas definidas antes de la primera línea
de código. Cada módulo se porta por separado desde la implementación anterior y solo entra cuando
cumple su definición de terminado: requisitos EARS, tests de comportamiento, sin historia en el
código y respetando las fronteras.

## Alternativas descartadas

- **Limpiar en sitio la implementación anterior.** Cada paso toca varios paquetes a la vez; no hay
  forma de trabajar un módulo aislado.
- **Escribirlo todo nuevo.** Se descartó entonces porque renunciaba a lo aprendido en la
  implementación anterior. El [ADR-0008](0008-built-new-nothing-is-ported.es.md) lo revierte.

## Consecuencias

- La parte de esta decisión que sigue vigente es el repositorio vacío con fronteras y puertas
  definidas primero. El porte no: no se portó ningún módulo, y el
  [ADR-0008](0008-built-new-nothing-is-ported.es.md) lo sustituye.
