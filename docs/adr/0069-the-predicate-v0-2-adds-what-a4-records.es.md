<!-- translation-of: 0069-the-predicate-v0-2-adds-what-a4-records.md sha256:21ca2ee42a4e1716 -->
# ADR-0069 · El predicado v0.2 añade lo que registra A4

**Estado:** aceptada

## Contexto

La [ADR-0064](0064-the-evidence-of-a3-is-an-unsigned-statement-with-a-closed-predicate.es.md) fijó
el predicado v0.1, enmendado por la
[ADR-0065](0065-the-evidence-of-a3-lists-every-gate-of-the-audit-flow.es.md) y la
[ADR-0066](0066-the-untrusted-texts-of-the-evidence-are-bounded.es.md); dice que un bloque que añade
un campo cambia la versión, y que un fichero de la v0.1 sigue pudiéndose leer como tal. A4 tiene
cuatro cosas que registrar para las que la v0.1 no tiene sitio:

- **la imagen del cambio**: `visible-examples` observa en una imagen construida con el árbol del
  cambio, cuya huella A3 guarda solo en el registro;
- **las ejecuciones de la verificación**, cuando la puerta `repeatability` la ejecute tantas veces
  como diga `verification.runs` de la política;
- **el commit del arnés** ([ADR-0068](0068-the-harness-is-named-by-its-version-and-its-commit.es.md));
- **un mensaje fiable para cada hallazgo**, que la separación fina de los mensajes rellenará más
  adelante; hasta entonces el mensaje entero sigue en `untrusted`.

El roadmap pidió que fueran en una sola versión, para que la versión cambie una vez.

## Decisión

**La regla.** Una versión del predicado solo añade campos: nunca cambia lo que significa un campo de
una versión anterior, y un fichero se lee con el esquema de su propia versión.

**El mecanismo en A4.** El tipo de predicado
`https://github.com/rafaranaz/raclab-dokime/attestation/conformance/v0.2` es el esquema cerrado de
la v0.1 con cuatro campos añadidos, cada uno ausente cuando la ejecución no lo rellena, nunca a
`null`:

| Campo | Qué guarda |
|---|---|
| `verifier.commit` | El commit del arnés, 40 caracteres hexadecimales en minúsculas. |
| `inputs.change_image` | La imagen del cambio en la que observó `visible-examples`: `digest`, y `platform` cuando su imagen base tiene uno. |
| `repeated` | `runs`, cuántas veces se ejecutó la verificación, y `consistent`, si todas las ejecuciones dieron el mismo veredicto, como lo nombra la arquitectura. |
| `message` de un hallazgo | Solo las palabras de dokime, fiable y opcional. Ningún módulo lo rellena en A4; el mensaje entero sigue en `untrusted`. |

- `evidence` escribe la v0.2 desde A4.
- Su lector lee un fichero de la v0.1 con el esquema de la v0.1 y uno de la v0.2 con el de la v0.2,
  y rechaza cualquier otro tipo de predicado.

## Base

Razonamiento, sin prueba: añadir campos mantiene legible todo fichero anterior, y un campo que ningún
módulo rellena todavía, `message`, evita que la separación fina vuelva a cambiar la versión cuando
llegue. La prueba es el lector, que relee un fichero de cada versión.

## Alternativas consideradas

- **Una v0.2 sin `message`, y una v0.3 con él cuando llegue la separación fina.** La versión
  cambiaría dos veces, lo que el roadmap pidió evitar.
- **La imagen del cambio en lugar de `inputs.image`.** Cambiaría lo que significa un campo de la
  v0.1, y `baseline` y el entorno usan la imagen de la base.
- **Cada valor nuevo como campo informativo**, el `informative` de la arquitectura, sin versión
  nueva. Una puerta no puede leer un campo informativo, y estos valores cambian lo que la evidencia
  dice que se comprobó.

## Consecuencias

- El lector de `evidence` mantiene dos esquemas, uno por versión.
- Un campo que ningún módulo rellena está en el esquema: `message` está siempre ausente en A4.
- `repeated` solo está presente cuando se ejecutó `repeatability`, así que la evidencia de una
  ejecución que se detuvo antes de la verificación lo omite.
