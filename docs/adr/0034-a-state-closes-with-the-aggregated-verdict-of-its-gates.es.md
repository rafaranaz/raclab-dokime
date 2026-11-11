<!-- translation-of: 0034-a-state-closes-with-the-aggregated-verdict-of-its-gates.md sha256:4f1d679d3cdbf193 -->
# ADR-0034 · Un estado se cierra con el veredicto agregado de sus puertas

**Estado:** propuesta

## Contexto

El [ADR-0018](0018-the-flow-is-a-state-machine-in-a-yaml-file.es.md) habla de "la puerta que
cierra" cada estado, en singular. El [ADR-0015](0015-a-gate-returns-one-of-four-verdicts.es.md)
agrega los veredictos de las puertas de una ronda: cualquier `FAIL` descarta los `ASK` de esa
ronda. Al escribir los primeros flujos se vio que los dos no encajan si un estado tiene
exactamente una puerta. La verificación son varias puertas cuyos veredictos hay que ver juntos, y
la evidencia tiene que listar cada una.

## Decisión

- Un estado de trabajo lista una o más puertas. Se ejecutan todas, en el orden escrito.
- El estado se cierra con la agregación de sus veredictos según la precedencia del ADR-0015, y el
  flujo sigue la transición de ese resultado.
- La evidencia lista cada puerta por separado, con su estado.
- Donde el ADR-0018 dice "la puerta que cierra cada uno", se lee "las puertas que cierran cada
  uno".

## Base

Razonamiento a partir de dos decisiones aceptadas. Con una puerta por estado, un `FAIL` en un
estado posterior no podría descartar un `ASK` planteado en uno anterior, porque el flujo ya se
habría detenido a preguntar; la agregación por ronda necesita que la ronda sea una unidad del
flujo. No se ha buscado ninguna fuente externa: es un punto de coherencia interna.

## Alternativas consideradas

- **Una puerta por estado, como está escrito.** Cada puerta pasa a ser un estado. La agregación
  necesita entonces que el flujo lleve veredictos de un estado al siguiente, que es lógica en el
  fichero.
- **Una puerta compuesta por estado.** La verificación sería una sola puerta con partes. La
  evidencia no podría decir que una parte opcional se omitió, y INV-7 lo exige puerta a puerta.

## Consecuencias

- El esquema del flujo tiene una lista de puertas por estado.
- Un flujo puede agrupar o separar puertas en estados para decidir cuándo se pregunta a una
  persona.
- Las puertas de un estado se ejecutan aunque una falle, de modo que la realimentación cubre la
  ronda entera.
