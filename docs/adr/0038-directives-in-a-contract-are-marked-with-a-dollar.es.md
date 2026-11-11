<!-- translation-of: 0038-directives-in-a-contract-are-marked-with-a-dollar.md sha256:622bc9a80a77a4da -->
# ADR-0038 · Las directivas de un contrato se marcan con un signo de dólar

**Estado:** aceptada

## Contexto

Un ejemplo mezcla datos con instrucciones para el arnés: compara este número con una tolerancia,
este texto tiene varias líneas y no acaba en salto de línea, esta salida es JSON. Las dos cosas se
escribían como mapas (`{approx: 10.03, tolerance: 0.005}`), así que una instrucción no se
distinguía de un dato. En la frontera `function` los datos son arbitrarios: una función puede
recibir o devolver un mapa con una clave `approx` o `text`. Los contratos escritos a mano del hito
A0 no usaron ningún comparador, y por eso la colisión no se vio.

## Decisión

- Un mapa con una clave que empieza por `$` es una **directiva**. Tiene exactamente una clave así,
  que da nombre a la directiva; sus otras claves son sus parámetros. Una directiva o un parámetro
  desconocidos son un hallazgo.
- Cualquier otro mapa es un dato, tal como está escrito.
- La lista de directivas es cerrada:

| Directiva | Parámetros | Significado | Dónde |
|---|---|---|---|
| `$text` | `final_newline` (obligatorio) | Un texto de varias líneas, escrito como bloque literal. `final_newline: false` quita el salto de línea que añade el bloque; `true` lo conserva | Entradas y expectativas |
| `$json` | — | Un texto que contiene este valor escrito como JSON | Entradas y expectativas |
| `$literal` | — | El valor es un dato tal como está escrito, aunque tenga claves que empiecen por `$` | Entradas y expectativas |
| `$any`, `$approx` (`tolerance`), `$unordered`, `$contains`, `$pattern`, `$ref` | — | Los comparadores del [ADR-0012](0012-examples-are-observations-at-a-boundary.es.md) | Solo expectativas |

- Un bloque literal aparece solo como valor de `$text`.
- Un texto que el bloque no puede expresar (acaba en varios saltos de línea, tiene retornos de
  carro o espacios al final de una línea) se escribe en una línea, entre comillas dobles, con
  escapes.

## Base

Comprobado: MongoDB marca sus operadores con `$`, ofrece `$literal` para tratar un valor como
dato, y desaconseja los nombres de campo que empiezan por `$` porque algunas funciones no los
admiten. Así que la convención existe en un sistema muy usado, con el mismo escape y con un coste
conocido. Comprobado con el prototipo del lector: una clave como `$approx` o `$text` se lee como
una clave normal en estilo de bloque y en estilo de flujo.

De memoria, sin comprobar hoy: JSON Schema marca igual sus propias palabras clave (`$ref`, `$id`).
Razonamiento: una marca en la clave la ve quien aprueba, y los datos con claves así son raros. Sin
prueba: los contratos de A0 no usaron comparadores. El primer contrato del corpus que use uno es
esa prueba.

## Alternativas consideradas

- **Etiquetas de YAML (`!approx 10.03`).** Están hechas para esto, pero el
  [ADR-0037](0037-a-contract-is-read-by-strict-rules-of-its-own.es.md) prohíbe las etiquetas, los
  parámetros no caben en un escalar y menos gente sabe leerlas.
- **Por posición: un comparador es lo que aparece dentro de `expect`.** No sirve cuando el valor
  esperado es él mismo un mapa con esa clave.
- **Envolver todos los datos (`{value: …}`).** Sin colisión, y cada ejemplo dobla su tamaño.

## Consecuencias

- Los comparadores conservan su significado y cambian de escritura: `{approx: …}` pasa a ser
  `{$approx: …}`.
- Un dato con una clave que empiece por `$` hay que envolverlo en `$literal`.
- El documento de arquitectura y los contratos de A0 se reescriben con las directivas.
