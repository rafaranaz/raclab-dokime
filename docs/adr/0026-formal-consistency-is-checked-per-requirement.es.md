<!-- translation-of: 0026-formal-consistency-is-checked-per-requirement.md sha256:c642e3ca36a6edb3 -->
# ADR-0026 · La consistencia formal se comprueba por requisito, y sus hallazgos preguntan

**Estado:** aceptada

## Contexto

Un solucionador puede encontrar contradicciones entre requisitos. La evidencia es para requisitos
de control sobre variables booleanas y numéricas con un esquema de variables hecho a mano; la
mayoría de los requisitos de una aplicación corriente no tienen esa forma. La formalización la
escribe un modelo.

## Decisión

- Las contradicciones que no necesitan modelo se comprueban siempre
  ([ADR-0011](0011-contract-of-requirements-and-approved-examples.es.md)).
- Desde la primera versión de la especificación, un solucionador (Z3) comprueba los requisitos que
  se pueden escribir como reglas sobre variables tipadas, uno a uno. La política lo activa.
- Un requisito se formaliza varias veces con variación; las formalizaciones que no son
  equivalentes lo marcan como ambiguo.
- Sus hallazgos son de origen `model`: preguntan a una persona, no rechazan.

## Base

Literatura. Una auditoría con solucionador detectó entre el 97 % y el 98 % de los defectos
inyectados en 64 requisitos de un dispositivo médico y marcó el 18,8 % como ambiguos comparando
cinco formalizaciones; no maneja requisitos temporales
([estudio](https://arxiv.org/abs/2605.13817), dos especificaciones).

## Alternativas consideradas

- **Un solucionador para todos los requisitos.** La mayoría no se formalizaría, o se simplificaría
  de más.
- **Un interruptor por tipo de proyecto.** Demasiado grueso: dentro de un proyecto unos requisitos
  se formalizan y otros no.
- **Hallazgos que rechazan.** El rechazo descansaría en una formalización que nadie revisó.

## Consecuencias

- Tiene que existir un esquema de variables para los requisitos que usen el solucionador.
- Los requisitos temporales se saltan y se listan como no comprobados.
