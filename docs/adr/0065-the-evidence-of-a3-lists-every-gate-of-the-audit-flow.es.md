<!-- translation-of: 0065-the-evidence-of-a3-lists-every-gate-of-the-audit-flow.md sha256:eb745d8a79eaeb04 -->
# ADR-0065 · La evidencia de A3 lista todas las puertas del flujo de auditoría, alcanzadas o no

**Estado:** aceptada

## Contexto

La [ADR-0064](0064-the-evidence-of-a3-is-an-unsigned-statement-with-a-closed-predicate.es.md) hace
que el predicado liste "cada puerta del estado, en su orden, tal como la lista la agregación", con
los estados `run` y `not-applicable`. La evidencia es de una ejecución, y una ejecución del flujo de
auditoría pasa por cinco estados con once puertas
([`04-states-and-flows.md`](../architecture/04-states-and-flows.es.md#el-flujo-de-auditoría)). Una
ejecución que una puerta detiene no alcanza las puertas siguientes, y la v0.1 no tiene estado para
ellas.

La sesión que revisa el trabajo probó el lector de la evidencia con doce ficheros manipulados a
mano. Uno de los que aceptaba tenía `gates: []` y el veredicto `PASS`. La comprobación del
veredicto contra las puertas que se ejecutaron, añadida después, rechaza ese fichero. No rechaza un
predicado que omite algunas puertas del flujo o las lista en otro orden.

La [ADR-0023](0023-evidence-is-an-attestation-bound-to-the-tree.es.md) y
[`03-data-and-evidence.md`](../architecture/03-data-and-evidence.es.md#la-evidencia) ya nombran
cuatro estados: `run`, `skipped`, `not-applicable` y `not-reached`. Una puerta es `not-reached` solo
en una ejecución que una puerta anterior detuvo.

## Decisión

Esta ADR enmienda la ADR-0064 en las puertas del predicado.

- **Las puertas del predicado son exactamente las del flujo de auditoría de A3, en su orden:**
  `contract`, `environment`, `baseline`, `protected-paths`, `existing-tests`, `visible-examples`,
  `relations`, `changed-line-coverage`, `behaviour-differences`, `repeatability` y
  `sealed-examples`. La lista es una constante de `evidence`, y el lector rechaza cualquier otra
  lista de nombres, orden o número.
- **El estado `not-reached` entra en el esquema**, con `gate`, `status` y `reason`. Una puerta
  `not-reached` tiene que venir después de una puerta que se ejecutó con un veredicto distinto de
  `PASS`, y ninguna puerta se ejecuta después de una `not-reached`. Una puerta que A3 no construye es
  `not-applicable`, alcanzada o no.
- **`skipped` queda fuera de la v0.1**, porque ninguna puerta de A3 es opcional en la política.
- **`interfaces` construye las puertas de la ejecución con la misma lista.** Un test del paso 11
  comprueba que las puertas que pasa a la agregación de cada estado, unidas en el orden de los
  estados, son la constante de `evidence`.

## Base

Los cuatro estados y la regla de `not-reached` ya están en la ADR-0023 y en la arquitectura. La
lista de puertas es la del flujo de auditoría de la arquitectura. Lo único que se decide aquí es
que la evidencia de A3 los usa.

Razonamiento, sin prueba: una lista fijada en `evidence` es la comprobación que un lector
independiente puede hacer de las puertas. La ADR-0023 hace que el verificador compruebe las puertas
contra el fichero de flujo, y A3 no tiene fichero de flujo.

## Alternativas consideradas

- **`audit` ejecuta todas las puertas que construye aunque una falle, para que ninguna quede sin
  alcanzar.** Contradice el flujo de auditoría, donde un `FAIL` va a `failed`, y ejecutaría los
  tests de un cambio cuyo contrato ya ha fallado.
- **El lector recibe la lista de puertas de quien lo llama.** Quien construye la evidencia sería
  quien dice qué puertas debería tener, y un lector independiente no tendría lista.
- **Cada estado lista solo sus puertas, y la ejecución lista los estados que alcanzó.** Necesita un
  campo para los estados, que la v0.1 no tiene, y deja sin nombrar las puertas no alcanzadas.

## Consecuencias

- La evidencia de una ejecución que se detiene nombra cada puerta que no alcanzó, con el motivo.
- `evidence` guarda una segunda copia de la lista del flujo de auditoría, después de la de la
  arquitectura. Cuando exista el fichero de flujo, la lista saldrá de él y la evidencia registrará
  su huella.
- Las ejecuciones de los tests de `evidence` listan las once puertas.
- El test del paso 11 ata la lista de `interfaces` a la de `evidence`.
