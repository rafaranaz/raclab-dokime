<!-- translation-of: 0064-the-evidence-of-a3-is-an-unsigned-statement-with-a-closed-predicate.md sha256:cba285a81622c14e -->
# ADR-0064 · La evidencia de A3 es un statement sin firmar con un predicado cerrado

**Estado:** propuesta

## Contexto

La [ADR-0023](0023-evidence-is-an-attestation-bound-to-the-tree.es.md) decide que la evidencia es
un statement de in-toto en un sobre DSSE, con un predicado propio. Deja como consecuencia que "los
campos del predicado tienen que fijarse antes de que el primer bloque escriba evidencia". A3 es ese
bloque: `audit` verifica un cambio que llega ya hecho y escribe su evidencia. Las firmas son del
bloque E, y también las aprobaciones de contratos. Varios campos del ejemplo de
[`03-data-and-evidence.md`](../architecture/03-data-and-evidence.es.md#la-evidencia) no tienen
nada que guardar en A3: no hay agente, ni intentos, ni ejemplos sellados, ni fichero de flujo, ni
ejecuciones repetidas.

Los hallazgos de las puertas citan texto que dokime no escribió: los valores observados y
esperados de un ejemplo, los nombres de los tests, las rutas del parche. Desde A4 la evidencia va a
las pull requests, donde la leen personas y agentes, y un valor citado puede llevar Markdown o
instrucciones para un modelo (T3 de la [ADR-0010](0010-threat-model.es.md)).

## Decisión

**El sobre y el fichero.**

- **En A3 la evidencia es solo el Statement v1 de in-toto, sin sobre.** El sobre DSSE y sus firmas
  llegan con el bloque E.
- **El fichero se llama `<story>.statement.json`.** El sufijo `.intoto.jsonl` se reserva para los
  bundles de sobres firmados del bloque E.
- **Sus bytes son la forma canónica de la
  [ADR-0062](0062-a-digest-is-taken-over-a-restricted-canonical-json.es.md)**, y el evento
  `evidence.built` del ledger guarda la huella de esos bytes.
- **El módulo `evidence` construye los bytes y los relee contra su esquema.** El módulo que los
  escribe los pone fuera del árbol que describen, como dice `03-data-and-evidence.md`.
- **El comando que verifica un fichero de evidencia se construye en el bloque E**, porque lo
  primero que comprueba son las firmas.

**El statement.**

- **`subject`** guarda el árbol, como `{"gitTree": …}`, y `change.patch`, como `{"sha256": …}`. El
  árbol es el de la base con el parche entero aplicado, es decir, el resultado del cambio. No es el
  árbol compuesto de la
  [ADR-0058](0058-existing-tests-runs-the-tests-of-the-base-on-the-code-of-the-patch.es.md), que es
  cómo se ejecuta una puerta.
- **`predicateType`** es `https://github.com/rafaranaz/raclab-dokime/attestation/conformance/v0.1`.

**El predicado v0.1 tiene un esquema cerrado.** Un campo desconocido se rechaza. Un campo que A3 no
puede rellenar está ausente, nunca a `null`. Un campo al que la ejecución no llegó también está
ausente, como la imagen cuando no se pudo construir el entorno; la puerta cuyo hallazgo detuvo la
ejecución dice por qué.

| Campo | En A3 |
|---|---|
| `verdict` | El veredicto de la agregación del estado ([ADR-0015](0015-a-gate-returns-one-of-four-verdicts.es.md)). |
| `delivered` | `false`: `audit` no entrega nada. |
| `independence` | `self-attested`. |
| `verifier` | `harness`, la versión del paquete, y `ran_on`, `developer`. |
| `contract` | `story`, y `digest`: `sha256:` y el SHA-256 de los bytes del fichero del contrato. `approval` está ausente hasta el bloque E. |
| `inputs.base` | El nombre del commit base. |
| `inputs.image` | `digest`, de la imagen construida, y `platform`, la huella del manifiesto de la plataforma de la imagen base tal como la da el runtime; `platform` está ausente cuando la etapa final parte de `scratch`. |
| `inputs.pack` | `digest`, `sha256:` y el SHA-256 de los bytes del fichero del pack. `level` está ausente hasta que existan los niveles. |
| `inputs.policy` | `digest`, de la forma normalizada de la política efectiva, y `source`, `file` o `defaults` ([ADR-0054](0054-the-policy-is-an-optional-file-of-values.es.md)). |
| `inputs.probe` | La huella del programa que observa los ejemplos ([ADR-0063](0063-a-program-of-sandbox-observes-the-examples-inside-the-zone.es.md)). |
| `gates` | Cada puerta del estado, en su orden, tal como la lista la agregación. |
| `human_decisions` | `[]`. |
| `not_checked` | Obligatorio, rellenado mecánicamente. |
| `ledger` | `head`, el hash del último evento antes de `evidence.built`, y `events`, cuántos hay hasta él. |

`author`, `attempts`, `repeated`, `inputs.flow`, `inputs.seeds` e `informative` están ausentes en
A3. Cada uno llega con el bloque que tiene algo que poner en él, y entonces cambia la versión del
predicado.

**Cada puerta.**

- Una puerta que se ejecutó tiene `gate`, `status: "run"`, su `verdict` y sus `findings`. Tiene
  también `checks`, una entrada por cada origen con el número de sus comprobaciones (`existing`
  para los tests; `human`, `derived` o `model` para los ejemplos), cuando la puerta ejecuta
  comprobaciones.
- Una puerta que no aplica tiene `gate`, `status: "not-applicable"` y su `reason`.
- Un hallazgo tiene `code`, `verdict`, `lines`, `message` y `untrusted`.
  - **`message` lleva solo palabras de dokime**, y los identificadores que el lector estricto del
    contrato ha comprobado contra su patrón.
  - **`untrusted` lleva todo texto que dokime no escribió**, como una lista de `{label, text}`. La
    etiqueta es una palabra de dokime, como `expected`, `observed`, `test` o `path`. El texto es un
    dato y quien lo muestre tiene que escaparlo. Cada texto se corta a 200 caracteres.

**Lo que no se comprobó en A3.** Cada entrada tiene `code`, `what`, `reason` y, cuando nombra algo
que dokime no escribió, `untrusted`.

| Código | Una entrada por | Motivo |
|---|---|---|
| `no-holdout` | Cada requisito | No hay ejemplos sellados hasta el bloque B. |
| `requirement-without-example` | Cada requisito sin ejemplo | Del contrato. |
| `only-model-checks` | Cada requisito cuyos ejemplos son todos de origen `model` | Del contrato. |
| `test-excluded-unstable` | Cada test cuyo resultado varió entre las ejecuciones de la base; su nombre va en `untrusted` | [ADR-0017](0017-damage-outside-the-change-against-a-baseline.es.md). |
| `example-unstable` | Cada ejemplo cuyo resultado varió entre las ejecuciones de la base | Un código nuevo de la lista, que según la arquitectura "empieza por" los códigos que nombra. |
| `outside-threat-model` | `existing-tests` | Los tests se ejecutan en el proceso del código evaluado ([ADR-0010](0010-threat-model.es.md)). |
| `outside-threat-model` | `baseline` y `visible-examples`, una entrada cada una | El código evaluado se ejecuta en el proceso que lo observa y puede reescribir lo observado ([ADR-0063](0063-a-program-of-sandbox-observes-the-examples-inside-the-zone.es.md)). |

## Base

Comprobado en las especificaciones:

- Un [Statement v1 de in-toto](https://github.com/in-toto/attestation/blob/main/spec/v1/statement.md)
  exige `_type`, `subject`, cada entrada con su `digest`, y `predicateType`. El `predicate` es
  opcional.
- [`gitTree`](https://github.com/in-toto/attestation/blob/main/spec/v1/digest_set.md) es un
  algoritmo de huella de la lista, en hexadecimal en minúsculas, válido para cualquier árbol.
- Un sobre DSSE sin firmas no verifica. El
  [protocolo](https://github.com/secure-systems-lab/dsse/blob/master/protocol.md) rechaza cuando
  las claves aceptadas son menos que el umbral, y el
  [modelo de validación](https://github.com/in-toto/attestation/blob/main/docs/validation.md) de
  in-toto rechaza cuando no hay firmantes. Algunas implementaciones construyen un sobre vacío como
  paso previo a firmar ([atlas-cli](https://docs.rs/atlas-cli/0.3.0/src/atlas_cli/in_toto/dsse.rs.html)),
  y otras lo rechazan al verificar
  ([nono](https://docs.rs/crate/nono/0.42.0/source/src/trust/dsse.rs)).
- La [especificación de bundles](https://github.com/in-toto/attestation/blob/main/spec/v1/bundle.md)
  dice que "Bundles SHOULD use the suffix `.intoto.jsonl`" y que cada línea "SHOULD be an
  Envelope". La sesión que revisa el trabajo encontró herramientas que ya llaman
  `<sha>.intoto.json` a un sobre DSSE.
- El [resumen de verificación de SLSA](https://slsa.dev/spec/v1.1/verification_summary) solo
  tiene `PASSED` y `FAILED` y ningún sitio para lo no comprobado, como ya decía la arquitectura.

Buscado y no encontrado: una especificación o una herramienta que defina cómo se guarda un
statement sin firmar como fichero final. La especificación ni lo prohíbe ni lo describe.

Razonamiento, sin prueba:

- **El nombre.** Un statement llamado `.intoto.json` parecería firmado a un lector y a las
  herramientas del ecosistema.
- **Ausente y no `null`.** Un `null` puede leerse como "comprobado y vacío", y el esquema sigue
  cerrado de las dos maneras.
- **`untrusted` aparte de `message`.** Quien muestre la evidencia puede escapar un campo y mostrar
  el otro tal cual, en vez de adivinar qué parte de un texto vino del código evaluado.
- **`ran_on` es `developer`.** Nada distingue una ejecución en CI hasta que exista la independencia
  `ci-verified`.
- **La huella del contrato y la del pack son las de sus bytes.** Es lo que una persona lee y, en el
  bloque E, aprueba. Ninguno tiene una forma normalizada, y la forma canónica de la ADR-0062 es
  para valores, no para ficheros.

La prueba que confirmaría la decisión es que un verificador de in-toto lea el statement cuando el
bloque E lo envuelva en un sobre. Se ejecuta en el bloque E.

## Alternativas consideradas

- **Un sobre DSSE con `signatures: []`.** Parece un formato firmado, y todo verificador lo
  rechaza.
- **El nombre `<story>.intoto.json`.** Sugiere un sobre firmado, que es lo que descarta la primera
  alternativa.
- **JSON con formato legible.** Su huella dependería de cómo se formatee, y el ledger guardaría la
  huella de unos bytes que tienen una segunda codificación.
- **Todos los campos presentes, con `null` donde no aplican.** Un `null` se lee como una
  respuesta.
- **Solo el veredicto de cada puerta, como en el ejemplo de la arquitectura, con los motivos en el
  ledger.** Un `FAIL` sin su motivo sirve de poco en una pull request, y el ledger no está a su
  lado.
- **Los hallazgos con el texto citado dentro de `message`, como hoy.** Quien los muestre no puede
  saber qué escapar.
- **El resumen de verificación de SLSA como predicado.** No tiene sitio para lo no comprobado.
- **El comando que verifica, construido ya sin firmas.** La mitad de lo que comprueba esperaría al
  bloque E, y su interfaz cambiaría entonces.

## Consecuencias

- El predicado v0.1 queda fijado para A3. Un bloque que añada un campo cambia la versión, y un
  fichero de evidencia v0.1 sigue pudiéndose leer como tal.
- La evidencia de A3 no está firmada, así que cualquiera puede escribir una a mano. Dice
  `self-attested`, y T6 de la ADR-0010 sigue fuera del modelo de amenazas.
- `Finding` en `core` gana el campo `untrusted`. Cada módulo cuyos hallazgos citan texto que dokime
  no escribió lo mueve ahí antes de que `evidence` escriba hallazgos: hoy `contract`, `packs`,
  `oracle`, `sandbox`, `platform`, `verify` e `interfaces`.
- El resultado de una puerta en `verify` gana sus comprobaciones por origen.
- `audit` escribe el fichero fuera del árbol. Dónde escribe por defecto se decide en `interfaces`.
- La verificación de un fichero de evidencia espera al bloque E. Hasta entonces, `evidence` solo
  relee lo que escribe.
