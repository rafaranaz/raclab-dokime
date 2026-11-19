<!-- translation-of: 0075-the-predicate-v0-3-records-the-hold-out.md sha256:1e60cc9522a5033d -->
# ADR-0075 · El predicado v0.3 registra la reserva

**Estado:** propuesta

## Contexto

En el bloque B el gate `sealed-examples` se ejecuta donde está la clave de la reserva
([ADR-0073](0073-the-key-of-the-hold-out-lives-outside-ci-until-b4.es.md)): lee el lote sellado, lo
comprueba contra el contrato y contra la historia del contrato, y observa los ejemplos reservados y
el canario sobre el árbol del cambio. El predicado v0.2
([ADR-0069](0069-the-predicate-v0-2-adds-what-a4-records.es.md)) no tiene sitio para lo que el
lector de la evidencia necesita para distinguir un pase con parte oculta de uno sin ella:

- **qué casos reservan un ejemplo y cuáles no**, y por qué: un caso de un solo ejemplo no tiene nada
  que reservar, y un caso cuyos ejemplos se publicaron todos antes del sellado los mantiene todos
  visibles ([ADR-0014](0014-hidden-checks-are-held-out-approved-examples.es.md));
- **qué ejemplos se mantuvieron visibles** por estar ya publicados;
- **qué lote sellado** comprobó el gate.

`not_checked` de la v0.1 y la v0.2 tiene el código `no-holdout`, una entrada por requisito con la
razón «There are no sealed examples until block B»
([ADR-0064](0064-the-evidence-of-a3-is-an-unsigned-statement-with-a-closed-predicate.es.md)). Su
grano es el requisito, y la reserva se decide por caso. Su lista cerrada tiene también el código
`best-effort-secrecy`, sin una fila que diga cuándo se escribe.

La reserva tiene dos partes de distinta fuerza. **La barrera** es lo que dokime hace y comprueba: la
orden que sella nunca escribe un ejemplo reservado en el árbol del proyecto; el lote se cifra para
los destinatarios de la base
([ADR-0072](0072-the-sealed-store-is-encrypted-with-age-for-a-list-of-recipients.es.md)) con una
clave fuera de CI; el agente nunca recibe un valor, una entrada ni el identificador de un ejemplo
reservado; el gate comprueba que el lote es el que el contrato nombra, por el digest con sal de cada
ejemplo reservado, por el reparto sacado de nuevo de la semilla, por su base en la historia del
cambio y por los ejemplos mantenidos visibles sacados de nuevo de esa base; y el canario detecta una
comparación que acepta una expectativa que no puede cumplirse. **La detección de un ejemplo
reservado ya publicado** es de mejor esfuerzo: lee las versiones del contrato de la historia en el
historial de git, y tiene límites.

## Decisión

**La regla.** La evidencia de un run sellado dice, caso por caso, si el caso tiene parte oculta y
por qué no, sin el valor de ningún ejemplo; y lista como no comprobado cada límite de la detección
de lo publicado. La barrera no se lista como no comprobada, porque el gate la comprueba: una barrera
rota es un hallazgo del gate, `sealed-batch-mismatch` o `canary-passed`; y un ejemplo reservado que
la detección encuentra publicado es también un hallazgo, `held-out-published`.

**El mecanismo en B1.** El tipo de predicado
`https://github.com/rafaranaz/raclab-dokime/attestation/conformance/v0.3` es el esquema cerrado de
la v0.2 con estas adiciones, cada una ausente cuando el run no la rellena, nunca `null`; la regla de
la ADR-0069 se mantiene: ningún campo ni código de una versión anterior cambia lo que significa.

| Adición | Qué contiene |
|---|---|
| `holdout` del gate `sealed-examples` | Presente cuando el gate observó, es decir, cuando el lote pasó sus comprobaciones. `batch`, el digest `sha256:` de los bytes de `sealed.age`; `held`, cada caso que reserva un ejemplo, como `{requirement, case}`; `kept_visible`, los ids de los ejemplos mantenidos visibles por estar ya publicados; `without_holdout`, cada caso que no reserva nada, como `{requirement, case, motive}`, con `motive` uno de `single-example` y `all-published`. Cada lista en el orden del contrato. Ningún id de un ejemplo reservado, ningún valor, ninguna entrada. |
| El código `case-without-holdout` de `not_checked` | Una entrada por cada caso de `without_holdout`: el requisito en `what`, el caso en un campo nuevo `case`, y como razón «the case has a single example» o «every example of the case was published before the seal». |
| La fila de `best-effort-secrecy` de `not_checked` | Cuando el gate observó, una entrada por cada límite de la detección, con `sealed-examples` en `what`: el contenido de un ejemplo se compara tal como lo lee YAML, así que uno publicado con un campo añadido o un valor escrito de otra forma no se reconoce; no se lee una versión con una ruta anterior, tras un renombrado; no se lee un commit que solo alcanzan otras refs; no se busca una copia de un ejemplo en otro fichero; y la auditoría lee la historia hasta la base de la pull request, así que un ejemplo reservado publicado en un commit de la pull request y retirado en otro no lo ve esa auditoría: en un proyecto que fusiona conservando los commits, por rebase o con un commit de fusión, lo ve la siguiente auditoría, y con una fusión squash no lo ve ninguna. |

- **Un código, un grano.** El constructor de la v0.3 no escribe `no-holdout`, que conserva su
  significado de la v0.1 y la v0.2, una entrada por requisito, en los ficheros de esas versiones. Un
  caso sin parte oculta es `case-without-holdout`.
- **Donde no está la clave**, el gate no es aplicable con la razón `the key is not here`
  (VERIFY-167), y la evidencia no tiene `holdout`, ni `case-without-holdout`, ni
  `best-effort-secrecy`: no se comprobó nada de la reserva, y el gate lo dice una vez. Tampoco se
  listan los casos sin parte oculta, aunque el contrato visible los diría: listarlos sería informar
  de una cobertura que el run no tiene. Un run que se detuvo antes del gate lo lista como no
  alcanzado, igual.
- **El orden de `not_checked`** es el de EVIDENCE-066 con `case-without-holdout` en el lugar de
  `no-holdout` y `best-effort-secrecy` al final; las entradas de `case-without-holdout` en el orden
  de los casos en el contrato, y las de `best-effort-secrecy` en el orden de la tabla.
- `evidence` escribe la v0.3 desde B1; su lector lee cada fichero con el esquema de su propia
  versión y rechaza cualquier otro tipo de predicado.

## Base

Razonamiento, sin test propio. El grano de la reserva es el caso (ADR-0014), así que la evidencia
tiene que nombrar el caso; un código con un solo grano por versión mantiene el significado de cada
fichero anterior, que es la regla de la ADR-0069. Los casos y los ids son nombres que el lector
estricto del contrato comprueba contra su patrón, así que son campos de confianza (ADR-0064). Los
límites son los que ya dicen los requisitos de `platform` y de `verify`; la evidencia solo los
lista. La prueba es el lector de `evidence`, que relee un fichero de cada versión, y un run del gate
cuya evidencia lista cada caso del contrato una sola vez, en `held` o en `without_holdout`.

## Alternativas consideradas

- **`no-holdout` por caso en la v0.3.** Cambiaría lo que significa un código de una versión
  anterior, que la ADR-0069 prohíbe, y un lector que cuente `no-holdout` entre versiones mezclaría
  requisitos y casos. Se consideró enmendar la regla de la ADR-0069 para permitirlo, y se descartó:
  la regla es lo que deja a un lector confiar en que un código significa una sola cosa.
- **`no-holdout` por caso donde está la clave y por requisito donde no.** Dos granos para un código
  en una versión; la ausencia de la clave ya es la razón del gate.
- **Solo `not_checked`, sin `holdout`.** `not_checked` lista lo que no se comprobó; los casos que sí
  reservan un ejemplo, los ejemplos mantenidos visibles y el digest del lote no tendrían sitio, y el
  lector no podría distinguir un caso con parte oculta de uno que la evidencia olvidó.
- **Los ids de los ejemplos reservados en `holdout`.** El contrato los nombra en `held_out`; la
  evidencia necesita el caso, y un id no añade nada que use el lector de la evidencia.
- **Una sola entrada de `best-effort-secrecy` con todos los límites en su razón.** Un lector no
  podría contar los límites, ni una versión posterior quitar uno cuando quede cubierto.
- **La barrera como entradas de `not_checked`.** Está comprobada, por el gate, y sus fallos son
  hallazgos; listarla como no comprobada diría lo contrario.

## Consecuencias

- El lector de `evidence` mantiene tres esquemas, uno por versión, y la lista cerrada de los códigos
  de `not_checked` difiere por versión: `case-without-holdout` no es un código de la v0.1 ni de la
  v0.2.
- `evidence` necesita, del run, los casos, los ejemplos mantenidos visibles y el digest del lote: el
  gate de `verify` tiene que entregarlos, y `interfaces` los lleva al run.
- La evidencia de un run sin la clave no dice nada de la reserva salvo la razón del gate. Los casos
  sin parte oculta podrían saberse sin la clave, porque las entradas de `held_out` del contrato
  visible nombran los casos que reservan un ejemplo, y el número de ejemplos visibles de cada otro
  caso da su motivo; no se listan porque en ese run no se comprobó nada de la reserva, y el gate ya
  lo dice una vez con su razón: listarlos sería informar de una cobertura que el run no tiene.
- Los límites de la detección están escritos en tres sitios: los requisitos de `verify`, su README y
  la evidencia. Un cambio de la detección cambia los tres.
- La tabla de la arquitectura en `03-data-and-evidence.md` tiene que nombrar `case-without-holdout`
  y el campo `holdout`, en una pull request de la arquitectura.
