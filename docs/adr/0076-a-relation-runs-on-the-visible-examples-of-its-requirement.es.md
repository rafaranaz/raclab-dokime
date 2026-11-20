<!-- translation-of: 0076-a-relation-runs-on-the-visible-examples-of-its-requirement.md sha256:b543869982ffb8de -->
# ADR-0076 · Una relación se ejecuta sobre los ejemplos visibles de su requisito

**Estado:** propuesta

## Contexto

La [ADR-0039](0039-what-a-contract-of-the-first-version-may-say.es.md) abrió el catálogo de
relaciones con `idempotent` y `order-insensitive`. Una relación tiene `id`, `requirement`,
`relation` y `target`, y `order-insensitive` tiene además `over`, la entrada cuyo orden no importa.
La primera versión comprueba su forma, y se ejecutan desde el bloque B. Una relación es una
comprobación de origen `derived` ([ADR-0013](0013-provenance-decides-what-a-check-can-do.es.md)):
aprobada por una persona y aplicada mecánicamente, y falla cuando no se cumple. La puerta
`relations` del estado `verifying` las ejecuta, y B2 la construye.

Sobre qué se ejecuta una relación no está decidido en ninguna parte:

- **las entradas de las que parte**, porque un contrato no da tipos con los que generar entradas;
- **qué significa `idempotent`** en `function` con más de un argumento, o en `cli`, donde la salida
  puede volver como entrada estándar o como los ficheros escritos;
- **cómo nombra `over` una entrada**, hoy cualquier texto de una línea;
- **cuántas permutaciones** prueba `order-insensitive`, y con qué semilla;
- **qué se le dice al agente** cuando una relación no se cumple, y **qué registra la evidencia**,
  porque el predicado v0.3 ([ADR-0075](0075-the-predicate-v0-3-records-the-hold-out.es.md)) no tiene
  sitio para la semilla de las relaciones ni para los órdenes que fallaron.

## Decisión

**La regla.** Una relación se ejecuta sobre los ejemplos visibles aprobados de su requisito y su
target, por un canal que la relación declara y que nunca se deduce; sus casos derivados se sacan
con una semilla que se registra, y su fallo le dice al agente dónde sin darle una entrada.

**El mecanismo en B2.**

- **Los casos de partida** son los ejemplos visibles del requisito de la relación, en su target, de
  un paso cada uno. Un ejemplo de más de un paso no es caso de partida. Un ejemplo reservado nunca
  lo es, porque la puerta `relations` se ejecuta donde puede no estar la clave.
- **`idempotent` declara su canal.**
  - En `cli`, el campo `via` dice `stdout`, para que la salida estándar de la ejecución de partida
    vuelva como entrada estándar de una segunda ejecución con los mismos argumentos, o `files`, para
    que la segunda ejecución, con los mismos argumentos, corra sobre los ficheros que escribió la
    primera.
  - En `function`, `over` nombra el argumento que recibe lo que devolvió la llamada de partida. Una
    función de un argumento no necesita `over`; con más de uno, `contract check` rechaza la relación
    sin él.
  - La relación se cumple cuando la segunda ejecución da lo que dio la primera: lo devuelto, o el
    código de salida y la salida estándar, o los ficheros escritos.
  - Un caso de partida cuya ejecución lanza una excepción, o sale con un código distinto de cero, no
    tiene caso derivado.
- **`over` nombra una entrada.** En `function` es `args[N]`, el argumento en esa posición contando
  desde cero, o el nombre de un argumento con nombre; para `order-insensitive`, lo que se permuta son
  los elementos de la lista que el ejemplo de partida da en ese argumento, y un caso de partida cuyo
  valor ahí no es una lista no tiene casos derivados. En `cli`, para `order-insensitive`, es
  `stdin`, cuyas líneas se permutan, o el nombre de un fichero de la entrada, cuyas líneas se
  permutan. `contract check` rechaza un `over` que no nombra ninguna entrada de la frontera del
  target.
- **`order-insensitive` permuta con una semilla.** Los casos derivados de un caso de partida son
  entradas, distintas entre sí y distintas de la entrada de partida, porque con elementos repetidos
  dos permutaciones dan la misma entrada y el orden inverso puede ser igual al de partida. Son el
  orden inverso, siempre que difiera del de partida, y hasta `relations.permutations` entradas
  distintas más sacadas con la semilla, 10 salvo que la política diga otra cosa
  ([ADR-0054](0054-the-policy-is-an-optional-file-of-values.es.md)); el tope es el número de
  entradas distintas que permiten los elementos, no n!. Un caso de partida cuyos elementos no
  permiten ninguna otra entrada no tiene casos derivados. La relación se cumple cuando cada caso
  derivado da lo que dio el de partida.
- **La semilla** de las relaciones es un entero natural de 53 bits aleatorios de la aleatoriedad
  del sistema, sacado en cada auditoría y registrado en su registro.
- **Una relación sin caso de partida** es un hallazgo `relation-without-source` con el veredicto
  `ASK`: el contrato pide una comprobación que ningún ejemplo puede alimentar. Lo es cuando no queda
  ningún ejemplo como caso de partida, sea porque ningún ejemplo visible de un paso tiene el
  requisito y el target, o porque ninguno tiene casos derivados: su ejecución lanza una excepción o
  sale con un código distinto de cero, en `idempotent`, o su entrada nombrada por `over` no es una
  lista o no permite ninguna otra entrada, en `order-insensitive`.
- **Una relación que no se cumple** es un hallazgo `relation-fails` con el veredicto `FAIL`, en la
  línea de la relación, cuyo mensaje da el requisito, la relación y el id del ejemplo visible de
  partida, y ni la permutación ni ningún valor.
- **La evidencia** escribe el predicado
  `https://github.com/rafaranaz/raclab-dokime/attestation/conformance/v0.4`, el esquema cerrado de
  la v0.3 con un campo añadido y la regla de la ADR-0069 mantenida. La entrada de la puerta
  `relations`, cuando se ejecutó, tiene `relations`: la `seed`, en claro, porque nada en ella es
  secreto, y `failed`, cada caso derivado que no se cumplió como `{relation, example}`, con `order`,
  para `order-insensitive`, una permutación que da su entrada, como lista de índices del orden de
  partida. No contiene
  ninguna entrada ni ningún valor.

## Base

**Verificado**, en las fuentes nombradas:

- Hypothesis ejecuta por defecto 100 casos que se cumplen (`max_examples`), fija su sorteo con
  `@seed` o, de forma determinista, con `derandomize`, activo por defecto en CI, y ante un fallo
  imprime el caso mínimo que falla después de reducirlo, con sus valores; `verbosity=quiet` no
  imprime nada. Su *ghostwriter* `idempotent()` escribe el test `f(f(x)) == f(x)` con estrategias
  deducidas de los tipos
  ([referencia de la API](https://hypothesis.readthedocs.io/en/latest/reference/api.html),
  [integraciones](https://hypothesis.readthedocs.io/en/latest/reference/integrations.html)).
- QuickCheck ejecuta por defecto hasta 100 pruebas, repite una ejecución a partir de su semilla y su
  tamaño, y avisa de que una semilla guardada por una versión no se repite en otra, así que un caso
  que se quiere conservar se conserva como caso; reduce el contraejemplo y lo imprime
  ([QuickCheck 2.19](https://hackage-content.haskell.org/package/QuickCheck-2.19.0.0/docs/Test-QuickCheck.html)).
- La mayoría de los estudios de pruebas metamórficas toman sus casos de partida de datos aleatorios
  o de suites de tests existentes; tres de ellos encontraron que los casos de partida aleatorios
  detectan más fallos que los diseñados a mano, y que combinar los dos los detecta antes; las buenas
  relaciones hacen que la ejecución derivada se aleje todo lo posible de la de partida; las
  relaciones de permutación son uno de los tipos habituales
  ([Segura et al., IEEE TSE 2016](https://eprints.whiterose.ac.uk/110335/1/segura16-tse.pdf), en su
  repaso de la generación de casos de partida).

**Buscado y no encontrado:** una herramienta que informe del fallo de una propiedad sin sus valores.
Hypothesis y QuickCheck hacen lo contrario, porque informan a una persona.

**Solo razonamiento:**

- El contrato no tiene tipos, así que no se pueden generar entradas sin un generador por target; los
  ejemplos visibles son las entradas que aprobó una persona. Son los casos de partida menos eficaces
  según los estudios de arriba, lo que se escribe como límite.
- `idempotent` tiene más de una lectura razonable en `cli` y en una función de varios argumentos;
  una lectura deducida por el arnés podría comprobar algo que la persona no quiso decir, así que lo
  dice la relación.
- El orden inverso es la permutación con más probabilidad de mostrar una dependencia del orden en
  una entrada corta, así que se prueba siempre; la semilla lo amplía, y la política acota el coste,
  porque cada caso derivado es una ejecución en el sandbox.
- Los ejemplos de partida son visibles, así que nada es secreto en la relación; al agente se le dice
  el ejemplo y no la permutación, para no darle una entrada concreta que tratar como caso especial.
- Los órdenes que fallaron se guardan como índices, como aconseja QuickCheck guardar casos y no
  semillas, sin escribir ningún valor en la evidencia.

La prueba es la medición de B2: en el corpus, un parche que rompe una relación de un caso falla la
puerta, y su parche bueno la pasa.

## Alternativas consideradas

- **Generar entradas para cada target**, como hace Hypothesis a partir de los tipos. El contrato
  necesitaría un generador o un tipo para cada entrada, un cambio de su formato; queda como mejora
  posible después de B3, donde el corpus muestra si bastan los ejemplos visibles.
- **Deducir el canal de `idempotent`** de la expectativa del caso de partida: salida estándar cuando
  espera `stdout`, ficheros cuando espera `files`. Un caso de partida que espera las dos cosas sería
  ambiguo, y la persona no vería qué se comprueba.
- **Un número fijo de permutaciones, o todas.** Todas crecen como n!; un número fijo no se puede
  ajustar al coste de un proyecto.
- **Decirle al agente la permutación que falló.** Es una entrada concreta que tratar como caso
  especial, y el requisito, la relación y el ejemplo bastan para buscar la dependencia del orden.
- **Registrar solo la semilla, sin los órdenes que fallaron.** Una semilla no se repite entre
  versiones del generador, que es el aviso de QuickCheck.
- **Una ADR aparte para el predicado v0.4.** El campo solo existe para esta puerta y se sigue de sus
  decisiones; el mantenedor pidió una sola ADR.

## Consecuencias

- `contract check` gana el campo `via` para `idempotent` y comprueba `over` contra la frontera del
  target; un contrato de la primera versión con una relación que no declara su canal donde hace
  falta no lo pasa.
- La política gana `relations.permutations`, y el coste de la puerta crece con el número de casos de
  partida y de permutaciones.
- Una relación solo se puede comprobar donde la alimenta un ejemplo visible de un paso; un requisito
  cuyos ejemplos son todos reservados o de varios pasos tiene `relation-without-source`.
- El lector de `evidence` mantiene cuatro esquemas, uno por versión.
- Las relaciones solo comprueban lo que alcanzan los ejemplos visibles, los casos de partida más
  débiles según los estudios; la puerta no dice nada de las entradas que ningún ejemplo cubre.
