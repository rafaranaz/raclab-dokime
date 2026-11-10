<!-- translation-of: 0001-record-decisions-in-adrs.md sha256:1317da31b535f791 -->
# ADR-0001 · Registrar las decisiones con ADR

**Estado:** aceptada

## Contexto

Cuando las decisiones quedan repartidas entre comentarios de código, documentos de plan, registros
de deuda técnica y mensajes de commit, averiguar por qué algo es como es exige leer la historia
entera, y el código acaba explicando su propio pasado en lugar de lo que hace.

## Decisión

Cada decisión con consecuencias se registra en un ADR en `docs/adr/`, numerado, con contexto,
decisión, alternativas descartadas y consecuencias. Un ADR aceptado no se edita: se sustituye por
otro nuevo que lo indica.

## Alternativas descartadas

- **Documentos de diseño vivos que se reescriben.** Pierden la razón por la que se descartaron las
  alternativas, que es justo lo que se necesita al revisar una decisión.
- **Decisiones en los mensajes de commit.** Son un buen complemento, pero no se pueden consultar por
  tema ni muestran qué decisiones siguen vigentes.

## Consecuencias

- Hay un sitio único y breve donde consultar por qué el sistema es como es.
- Escribir un ADR lleva un rato, así que se reserva para decisiones con consecuencias, no para cada
  cambio.
