<!-- translation-of: 0062-a-digest-is-taken-over-a-restricted-canonical-json.md sha256:2648f669f256a6dd -->
# ADR-0062 · Una huella se toma sobre un JSON canónico restringido, y un registro con hash se guarda en él

**Estado:** aceptada

## Contexto

Tres cosas del bloque A se identifican por la huella de un valor: cada evento del registro guarda
el hash del anterior ([ADR-0023](0023-evidence-is-an-attestation-bound-to-the-tree.es.md)), la
evidencia registra la política por la huella de su forma normalizada
([ADR-0054](0054-the-policy-is-an-optional-file-of-values.es.md)), y la huella de un contrato se
toma sobre las formas canónicas de sus partes
([`03-data-and-evidence.es.md`](../architecture/03-data-and-evidence.es.md)). Ninguna dice cuál es
la forma canónica, y ningún código la calcula. Dos programas que conviertan el mismo valor en bytes
distintos dan huellas distintas, y una cadena o una huella que otro programa no puede recalcular no
se puede verificar sin el arnés.

## Decisión

- **La forma canónica de un valor es su texto JSON según la RFC 8785 (JCS), restringida.** Las
  claves de cada mapa se ordenan por sus unidades de código UTF-16; no hay espacios; los caracteres
  que no son ASCII se escriben tal cual, sin escapar.
- **La restricción son los valores de I-JSON (RFC 7493) sin decimales**: textos, números enteros,
  booleanos, null, listas y mapas con claves de texto. Un número que no es entero, un entero fuera
  de ±(2^53 − 1) o un texto con un sustituto UTF-16 suelto se rechazan, no se redondean ni se
  reemplazan.
- **Una huella es `sha256:` y el SHA-256 en hexadecimal de la forma canónica en UTF-8.**
- **La forma canónica se escribe en el arnés**, en `core`, sin el paquete `rfc8785`.
- **Un registro con hash se guarda en su forma canónica, y quien lo verifica rechaza cualquier otra
  codificación.** En el registro de eventos, cada línea es exactamente la forma canónica de su
  evento con su `hash`, y el `hash` es la huella del evento sin ese campo; una línea que se lee como
  el mismo evento pero difiere en sus bytes se rechaza. Así nunca hay dos codificaciones de un
  evento.

## Base

Leído:

- DSSE, el sobre que usa in-toto, evita la canonicalización "por seguridad": quien verifica
  comprueba los bytes tal como se firmaron, antes de leerlos. Dejó el esquema anterior de TUF e
  in-toto porque dependía de JSON canónico, en el que "dos contenidos de significado distinto
  podrían tener la misma codificación canónica" y quien verifica tiene que leer antes de verificar
  ([DSSE, background](https://github.com/secure-systems-lab/dsse/blob/master/background.md)). La
  última regla de la decisión responde a eso en el registro: quien verifica compara bytes.
- La implementación de la RFC 8785 de Trail of Bits ordena las claves con `encode("utf-16be")`,
  rechaza los enteros fuera de ±(2^53 − 1) citando el apéndice B de la RFC, y rechaza los
  sustitutos sueltos al codificar en UTF-8
  ([rfc8785.py](https://github.com/trailofbits/rfc8785.py/blob/main/src/rfc8785/_impl.py)).
- Encontrado por la sesión que revisa el trabajo, sin comprobar más: implementaciones de un
  subconjunto de JCS que rechazan los decimales, como esta.
  [MPP.JCS](https://mpp.hexdocs.pm/MPP.JCS.html), en Elixir, es un subconjunto de JCS sin
  decimales; [jcs de musereel-sdk](https://pkg.go.dev/github.com/emiya-dev/musereel-sdk/jcs), en
  Go, acepta enteros y textos y rechaza las claves duplicadas, los decimales y los sustitutos
  sueltos.

Los tests de la forma canónica usan los vectores de la RFC 8785 que se aplican a la restricción: las
cadenas de la sección 3.2.2 y el orden de las claves de la sección 3.2.3; el apéndice B trata de
números con decimales y no se aplica. Llegan con el ámbito `core`.

Razonamiento, sin test: que ningún valor que el arnés convierte en huella en el bloque A necesita
un decimal, así que dejar fuera los números de ECMAScript quita la parte más difícil de JCS sin
perder nada; y que Python ordena las claves por puntos de código, lo que difiere de UTF-16 solo
para caracteres fuera del plano básico, así que la diferencia hay que escribirla y probarla, no
darla por resuelta.

## Alternativas consideradas

- **`json.dumps` con `sort_keys=True`.** No es un estándar, su orden de claves difiere del de JCS
  fuera del plano básico, y otro programa no podría estar seguro de reproducir una huella.
- **CBOR con la codificación determinista de la RFC 8949, sección 4.2.** Es binario, un registro
  en él no se puede leer como texto, y añade una dependencia.
- **El paquete `rfc8785`.** Una dependencia más para una función de unas decenas de líneas una vez
  fuera los decimales.
- **En el registro, hashear los bytes de cada línea y quitar el campo `hash`.** Evita la
  canonicalización en la cadena, como hace DSSE, pero cada evento dejaría de guardar su propio
  hash, que decide la ADR-0023; habría que enmendarla.

## Consecuencias

- El registro, la política y el contrato comparten una función de `core`, y un programa fuera del
  arnés puede recalcular sus huellas con cualquier implementación de JCS, dentro de la restricción.
- Un valor con un decimal no se puede convertir en huella; si un bloque posterior lo necesita, lo
  decide entonces.
- Un registro editado a mano, aunque solo sea en sus espacios, lo rechaza quien lo verifica.
- El lector del registro compara cada línea con la forma canónica de lo que leyó, así que lee antes
  de verificar; la comparación de bytes es lo que evita que eso sea una superficie de ataque.
