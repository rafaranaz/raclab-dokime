<!-- translation-of: 0015-a-gate-returns-one-of-four-verdicts.md sha256:cdc01a89ef8d9e64 -->
# ADR-0015 · Una puerta devuelve uno de cuatro veredictos

**Estado:** propuesta

## Contexto

Con dos veredictos, un resultado dudoso tiene que aprobarse o rechazarse, y un fallo del entorno
cuenta como fallo del cambio.

## Decisión

- Una puerta devuelve `PASS`, `FAIL`, `ASK` o `ERROR`.
- `ERROR` significa que la puerta no pudo evaluar. Se reintenta una vez; si persiste, se pregunta
  a una persona. Nunca pasa, y no marca el cambio como malo.
- Agregación por precedencia: algún `ERROR` sin resolver da `ERROR`; si no, algún `FAIL` da `FAIL`
  y los `ASK` de esa vuelta se descartan; si no, algún `ASK` da `ASK`; si no, `PASS`.
- Un cambio se entrega con `PASS`, o con `ASK` cuando una persona ha respondido cada pregunta. Las
  respuestas forman parte de la evidencia.

## Base

Razonamiento. Conserva la regla de que lo que no se puede evaluar no pasa, sin culpar al cambio de
un fallo ajeno.

## Alternativas consideradas

- **Dos veredictos, y una puerta que no puede evaluar rechaza.** Una infraestructura inestable
  consumiría intentos y rechazaría cambios buenos.
- **Tres veredictos sin `ERROR`.** La persona no distinguiría una duda sobre el cambio de un
  entorno roto.

## Consecuencias

- Todo consumidor de un veredicto tiene que tratar cuatro casos.
- En un modo sin preguntas, llegar a una pregunta termina la ejecución como rechazada con ese
  motivo.
