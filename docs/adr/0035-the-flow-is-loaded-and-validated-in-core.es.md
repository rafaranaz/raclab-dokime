<!-- translation-of: 0035-the-flow-is-loaded-and-validated-in-core.md sha256:91bd4281c0821b1d -->
# ADR-0035 · El flujo se carga y se valida en core

**Estado:** propuesta

## Contexto

El motor, que ejecuta un flujo con sus bucles, presupuestos y agente, se construye en el bloque C
([ADR-0029](0029-build-order-starts-with-auditing.es.md)). El bloque A ya produce evidencia, y la
evidencia lista cada puerta del flujo y lleva la huella del fichero de flujo (INV-7). Así que el
bloque A tiene que leer un fichero de flujo y saber que está bien formado, dos bloques antes de
que exista el motor.

## Decisión

- El esquema del flujo, su cargador y su validador forman parte de `core`. Son puros: reciben el
  texto del fichero y devuelven un flujo validado o la lista de lo que está mal.
- `engine` ejecuta un flujo validado: sigue transiciones, cuenta presupuestos, hace las preguntas
  y empaqueta la tarea para el agente.
- En el bloque A el flujo de auditoría no tiene bucles, y `verify` ejecuta sus estados en orden a
  partir del flujo validado.

## Base

Razonamiento a partir del orden de construcción y de INV-7. El validador no tiene entrada ni
salida propias, que es lo que `core` admite. No se ha buscado ninguna fuente externa.

## Alternativas consideradas

- **Dejarlo todo en el motor y fijar en código el flujo de auditoría para los bloques A y B.** La
  evidencia llevaría la huella de una constante, y el primer fichero de flujo real llegaría junto
  con los primeros bucles, que es el momento de más riesgo para estrenar el esquema.
- **Adelantar el motor al bloque A.** Trae presupuestos, preguntas y el agente al bloque cuyo
  sentido es no necesitar nada de eso.

## Consecuencias

- `core` crece con un esquema y un validador, y necesita un lector de YAML.
- Las reglas del validador se prueban desde el bloque A, primero sobre un flujo sin bucles.
- El mapa de módulos cambia: `core` carga y valida el flujo; `engine` lo ejecuta.
