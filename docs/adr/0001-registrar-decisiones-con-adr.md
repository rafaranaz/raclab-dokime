# ADR-0001 · Registrar las decisiones con ADR

**Estado:** aceptada

## Contexto

En `dokime` las decisiones quedaron repartidas entre comentarios de código, documentos de plan,
registros de deuda técnica y mensajes de commit. Reconstruir por qué algo es como es exigía leer la
historia entera, y el código acabó explicando su propio pasado en lugar de lo que hace.

## Decisión

Cada decisión con consecuencias se registra en un ADR en `docs/adr/`, numerado, con contexto,
decisión, alternativas descartadas y consecuencias. Un ADR aceptado no se edita: se sustituye por
otro que lo indica.

## Alternativas descartadas

- **Documentos de diseño vivos que se reescriben.** Pierden el porqué de lo que se descartó, que es
  justo lo que se necesita al revisar una decisión.
- **Decisiones en los mensajes de commit.** Son buen complemento, pero no se pueden consultar por
  tema ni ver cuáles siguen vigentes.

## Consecuencias

- Hay un sitio único y breve donde consultar por qué el sistema es como es.
- Escribir un ADR cuesta un rato; por eso solo se escribe para decisiones con consecuencias, no
  para cada cambio.
