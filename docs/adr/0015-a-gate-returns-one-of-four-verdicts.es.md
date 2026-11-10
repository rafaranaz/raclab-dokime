<!-- translation-of: 0015-a-gate-returns-one-of-four-verdicts.md sha256:a718c43e55dfd865 -->
# ADR-0015 · Una puerta devuelve uno de cuatro veredictos

**Estado:** aceptada

## Contexto

Con dos veredictos, un resultado dudoso tiene que aprobarse o rechazarse, y un fallo del entorno
cuenta como fallo del cambio.

## Decisión

- Una puerta devuelve `PASS`, `FAIL`, `ASK` o `ERROR`.
- `ERROR` significa que la puerta no pudo evaluar. Se reintenta una vez; si persiste, se pregunta
  a una persona. La persona puede arreglar el entorno y repetir la puerta, o abandonar el cambio;
  nadie puede dar el error por bueno. Nunca pasa, y no marca el cambio como malo.
- Una puerta solo se omite cuando la política la declara opcional. Omitir una puerta obligatoria
  es un `ERROR`. Las puertas omitidas se listan en la evidencia y en el pull request.
- Agregación por precedencia: algún `ERROR` sin resolver da `ERROR`; si no, algún `FAIL` da `FAIL`
  y los `ASK` de esa vuelta se descartan; si no, algún `ASK` da `ASK`; si no, `PASS`.
- Un cambio se entrega con `PASS`, o con `ASK` cuando una persona ha respondido cada pregunta. Una
  pregunta que plantea una puerta la responde una persona; una respuesta delegada no cuenta
  ([ADR-0025](0025-the-interview-works-on-files-and-ends-by-coverage.es.md)). Las respuestas
  forman parte de la evidencia.

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
- En un modo sin preguntas, llegar a una pregunta termina la ejecución como pendiente de una
  persona, con ese motivo. Ni rechaza ni pasa: el check del pull request queda pendiente hasta que
  una persona responde y la ejecución se repite.
