<!-- translation-of: 0008-built-new-nothing-is-ported.md sha256:22511693dbd237e6 -->
# ADR-0008 · El producto se construye nuevo; no se porta nada

**Estado:** propuesta

## Contexto

El [ADR-0002](0002-new-repository-ported-by-module.es.md) preveía portar una implementación
anterior módulo a módulo. Al revisar el diseño se vio que varias decisiones se habían traído de
esa implementación como si estuvieran cerradas, sin comprobar cómo resuelven los mismos problemas
las herramientas, los estándares y los estudios publicados. Tres revisiones independientes del
diseño cambiaron después su centro: el oráculo, el orden de construcción y el papel del agente.

## Decisión

- Cada módulo se diseña y se escribe nuevo, a partir de sus requisitos.
- Ningún documento, comentario o commit de este repositorio cita una implementación anterior como
  motivo. Una decisión se apoya en literatura, en razonamiento o en una prueba, y dice en cuál.
- Este ADR sustituye al ADR-0002.

## Base

Razonamiento. Una implementación anterior demuestra que una idea se puede escribir, no que
funcione.

## Alternativas consideradas

- **Portar módulo a módulo (ADR-0002).** Mantiene el coste bajo, pero también las suposiciones que
  nadie verificó, y el diseño que salió de las revisiones ya no coincide con los módulos antiguos.
- **Portar solo lo que todavía encaje.** Decidir qué encaja exige la misma verificación que
  escribirlo, sin la ventaja de partir de los requisitos.

## Consecuencias

- Más código que escribir, y ningún atajo para el primer bloque.
- Cada decisión se puede rastrear hasta su base y no hasta una costumbre previa.
- Los ADR aceptados 0001 a 0007 conservan su contexto original, porque un ADR aceptado no se edita.
