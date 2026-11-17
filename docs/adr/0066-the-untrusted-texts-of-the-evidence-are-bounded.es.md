<!-- translation-of: 0066-the-untrusted-texts-of-the-evidence-are-bounded.md sha256:4759c858e29ed242 -->
# ADR-0066 · Los textos no fiables de la evidencia están acotados

**Estado:** propuesta

## Contexto

La [ADR-0064](0064-the-evidence-of-a3-is-an-unsigned-statement-with-a-closed-predicate.es.md) pone
en `untrusted` todo texto que puede contener lo que dokime no escribió: en A3, el mensaje entero de
cada hallazgo y el nombre de cada test inestable. Tal como se propuso, cortaba cada uno de esos
textos en 200 caracteres. El corte desapareció del texto cuando la revisión de #119 sustituyó el
punto por el mensaje entero en `untrusted`. Fue un error de redacción, no una decisión.

Los mensajes miden más de 200 caracteres. Un hallazgo de un ejemplo que no se cumple cita hasta
cinco diferencias, cada una con su valor esperado y su valor observado cortados en 200 caracteres,
así que su mensaje puede llegar a unos 2.200 caracteres.

La sesión que revisa el trabajo probó el lector de la evidencia con doce ficheros manipulados a
mano. Uno de los que aceptaba tenía un texto no fiable de 500 caracteres.

## Decisión

Esta ADR enmienda la ADR-0064 en los textos de `untrusted`.

- **Un texto que la evidencia cita por sí misma**, como el nombre de un test (y más adelante una
  ruta), tiene como mucho **200 caracteres**.
- **El mensaje de un hallazgo**, con la etiqueta `message`, tiene como mucho **4.096 caracteres**.
- **El constructor corta un texto más largo** a un carácter menos que su límite, seguido de `…`,
  para que una ejecución nunca se rechace por la longitud de lo que cita.
- **El lector rechaza un texto más largo** con un hallazgo `evidence-schema` que nombra su sitio.
- **Un carácter es un punto de código de Unicode**, tal como lo escribe la forma canónica de la
  [ADR-0062](0062-a-digest-is-taken-over-a-restricted-canonical-json.es.md).

## Base

Razonamiento, sin prueba:

- **200 caracteres** es el límite que `verify` ya aplica a cada valor que cita.
- **4.096 caracteres** caben el mensaje más largo de las puertas de A3, unos 2.200, con margen.
- **Los límites mantienen la evidencia lo bastante pequeña para mostrarla** en una pull request en
  A4.

## Alternativas consideradas

- **200 caracteres para todo texto, también el mensaje.** Corta las diferencias que explican por
  qué falla un ejemplo.
- **Sin límite.** El nombre de un test o un valor observado puede ser tan largo como lo haga el
  código evaluado, y la evidencia va a las pull requests.
- **El constructor rechaza un texto demasiado largo en vez de cortarlo.** Una ejecución acabaría
  sin evidencia por algo que escribió el código evaluado.

## Consecuencias

- Un mensaje largo pierde su final en la evidencia.
- El lector puede rechazar un fichero cuyos textos se alargaron a mano.
