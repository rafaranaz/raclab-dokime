<!-- translation-of: 0039-what-a-contract-of-the-first-version-may-say.md sha256:d739b3e2a5596e51 -->
# ADR-0039 · Qué puede decir un contrato de la primera versión, y qué decide su comprobación

**Estado:** aceptada

## Contexto

El hito A1 comprueba un contrato y dice qué le falta. Al escribir sus requisitos se vio que el
formato dejaba varias cosas abiertas: qué fronteras acepta la primera versión, qué campos tiene un
ejemplo en cada una, si un ejemplo tiene que decir su origen, qué relaciones existen, qué son
exactamente una contradicción y un duplicado, y qué significa cada comparador. Una comprobación no
puede rechazar lo que el formato no define.

## Decisión

- **Fronteras.** La primera versión comprueba ejemplos en `function` y `cli`. Un ejemplo en
  `http`, o el comparador `$ref`, da un hallazgo `not-supported-yet` con el veredicto `ERROR`: el
  arnés no pudo evaluarlo, y no se culpa al contrato.
- **Origen.** Cada ejemplo dice su `origin`, `human` o `model`. No hay valor por defecto.
- **Relaciones.** El catálogo empieza con dos: `idempotent` y `order-insensitive`. Una relación
  tiene `id`, `requirement`, `relation` y `target`; `order-insensitive` tiene además `over`, la
  entrada cuyo orden no importa. La primera versión comprueba su forma; se ejecutan desde el
  bloque B. El catálogo solo crece por ADR.
- **Contradicción.** Dos ejemplos con la misma frontera, el mismo objetivo y las mismas entradas
  cuyas expectativas no pueden cumplirse a la vez. Dos valores exactos distintos se contradicen.
  Un valor exacto contradice a un comparador que no satisface. Dos comparadores no se comparan.
  Con varios pasos, se comparan los pasos con las mismas entradas desde el principio.
- **Duplicado.** Dos ejemplos con la misma frontera, el mismo objetivo y los mismos pasos, sean
  cuales sean su id, su caso y su descripción.
- **Un nombre cambia.** El comparador que el
  [ADR-0038](0038-directives-in-a-contract-are-marked-with-a-dollar.es.md) lista como `$pattern`
  se llama `$fullmatch`, como la función de Python que hace lo mismo.
- **Veredictos.** Un esquema roto, un texto de requisito que no es EARS, una contradicción y un
  duplicado dan `FAIL`. Un requisito sin ejemplo, o con ejemplos solo de origen `model`, da `ASK`
  ([ADR-0013](0013-provenance-decides-what-a-check-can-do.es.md)).

Los campos de un ejemplo son cerrados; uno desconocido es un hallazgo. Lo que `expect` no declara
no se compara, y un paso declara al menos una expectativa.

| Frontera | `target` | `input` | `expect` |
|---|---|---|---|
| `function` | `módulo:función` | `args` (una lista), `kwargs` (un mapa) | `returns` (un valor) o `raises` (`type`, el nombre de la excepción, y opcionalmente `message`) |
| `cli` | La orden | `args` (una lista de textos), `stdin` (un texto), `files` y `env` (mapas de un nombre a un texto) | `exit` (un entero), `stdout`, `stderr` (textos), `files` (un mapa de un nombre a un texto) |

Los comparadores de la primera versión:

| Comparador | Valor esperado | Se cumple cuando |
|---|---|---|
| `$contains` | Un texto | El texto observado lo contiene |
| `$fullmatch` | Una expresión regular de Python | Casa con el texto observado entero |
| `$approx`, con `tolerance` | Un número | El número observado difiere como mucho en `tolerance`, que es absoluta y obligatoria |
| `$unordered` | Una lista | La lista observada tiene los mismos elementos, en cualquier orden |
| `$any` | `uuid` o `timestamp` | El texto observado es un UUID, o una fecha y hora en ISO 8601 |

## Base

De los tres contratos escritos a mano del hito A0: usan `args`, `kwargs`, `returns`, `exit`,
`stdout` y `files`, una relación (`idempotent`) y un comparador (`$contains`). Los demás campos,
`order-insensitive` y los demás comparadores no se han usado en un contrato real.

Leído en las fuentes:

- Las herramientas se dividen en dos familias sobre qué tiene que casar un patrón. En cualquier
  parte del texto: `pattern` en JSON Schema, `raises(match=…)` en pytest y `assertRegex` en
  unittest, que buscan. El texto entero: el atributo `pattern` de HTML y, por una fuente
  secundaria, la faceta `pattern` de XML Schema. Quien escribe contratos para un proyecto Python
  viene de la primera familia.
- Así que un comparador llamado `$pattern` que casara el texto entero usaría la palabra de JSON
  Schema con el significado contrario. El texto entero sigue siendo el significado correcto aquí:
  un patrón demasiado estricto falla donde una persona lo ve, uno demasiado laxo pasa en silencio,
  y el bloque se mide por sus falsos aprobados. El nombre `$fullmatch` conserva el significado y
  quita el falso amigo. `$contains` ya cubre "en cualquier parte".
- `pytest.approx` (versión 9.2.0) compara por defecto con una tolerancia relativa de una
  millonésima. `$approx` no tiene valor por defecto: quien aprueba ve la tolerancia.
- `ERROR` para lo que la versión no puede comprobar se sigue del
  [ADR-0015](0015-a-gate-returns-one-of-four-verdicts.es.md): nunca pasa y no marca el cambio
  como malo.

Razonamiento, sin prueba: un `origin` obligatorio, porque un valor por defecto `human` daría una
confianza que nadie escribió; `FAIL` para un duplicado, porque infla el número de ejemplos por
caso que cuenta la reserva; fijar ya dos relaciones, igual que el hito A1 abrió `interfaces` antes
de tiempo ([ADR-0036](0036-a-milestone-may-open-an-increment-of-a-later-module.es.md)), para que
un nombre inventado se detecte desde la primera versión. No se ha buscado cómo definen otras
herramientas una contradicción entre ejemplos.

## Alternativas consideradas

- **`FAIL` para lo que todavía no está soportado.** Culparía al contrato de un límite de la
  herramienta.
- **Solo los campos que usó A0.** Una superficie menor, y el primer contrato con un caso de error
  o con entrada estándar exigiría un cambio de formato.
- **`origin` con `human` por defecto.** Una línea menos por ejemplo.
- **Comprobar solo la forma de las relaciones hasta el bloque B.** Un nombre de relación
  inventado pasaría la comprobación de la primera versión.
- **`$pattern` casando en cualquier parte, como JSON Schema y pytest.** Sin sorpresa para quien
  viene de ellos, y un patrón laxo aprueba en silencio.
- **`$pattern` casando el texto entero.** La primera decisión, tomada antes de mirar cómo lo hacen
  otras herramientas. Segura, con un nombre prestado que en otros sitios significa lo contrario.
- **Comparar dos comparadores.** Decidir si dos patrones pueden cumplirse a la vez no es posible
  en general; una respuesta parcial parecería completa.

## Consecuencias

- El significado de los comparadores vive en `contract`, porque la comprobación de
  contradicciones lo necesita; `oracle` lo usa desde ahí, cosa que las reglas de dependencia
  permiten.
- Los contratos de A0 ganan `origin: human` en cada ejemplo.
- Un contrato que necesite `http` o `$ref` no se puede comprobar hasta un bloque posterior, y la
  comprobación lo dice.
