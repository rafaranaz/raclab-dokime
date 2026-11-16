<!-- translation-of: 0057-the-cases-of-the-corpus-come-from-witnesses-that-fit-a-boundary.md sha256:c41184680dee6ddc -->
# ADR-0057 · Los casos del conjunto salen de testigos más allá del segundo, que caben en una frontera

**Estado:** aceptada

## Contexto

La [ADR-0055](0055-a-case-of-the-corpus-is-labelled-by-how-it-is-built.es.md) toma los parches
buenos del conjunto de casos de los testigos que encuentra la autocomprobación de un pack, y dice
que la autocomprobación, que para en el segundo testigo, da dos por proyecto, seis en total,
bastantes para los diez casos de A3; buscar más allá del segundo testigo solo haría falta en el
bloque B. El 2026-11-15 se leyeron los seis testigos uno a uno, y solo uno de ellos puede ser un
caso.

## Decisión

Esto enmienda la ADR-0055 en dos puntos; el resto se mantiene.

- **Buscar testigos más allá del segundo hace falta ya, para A3.** Se hace con un script que
  ejecuta el orden, los candidatos y la regla de un testigo del arnés (ADR-0044) sobre más
  candidatos. El script entra en el repositorio en el ámbito `corpus` cuando se abra A3, con su
  requisito, y sus resultados como fixture
  ([ADR-0050](0050-an-experiment-enters-the-repository-as-a-test.es.md)). La autocomprobación de un
  pack no cambia: sigue parando en el segundo testigo.
- **Un testigo pasa a ser un parche bueno solo si pasa dos filtros**, además de ser un testigo:
  - *aislado*: su cambio de código es el arreglo, no una refactorización ni un cambio de las
    herramientas de los tests;
  - *expresable*: lo que arregla se puede escribir como ejemplos en una frontera de la primera
    versión del contrato ([ADR-0039](0039-what-a-contract-of-the-first-version-may-say.es.md)): una
    función de un módulo llamada con valores de JSON, o una línea de órdenes.

  Un testigo que no pasa un filtro se registra con el motivo, porque la proporción que no pasa el
  segundo es una medida en sí misma.
- **El parche bueno es todo lo que el commit cambia fuera de las rutas de los tests del pack**,
  documentación incluida, y no solo el código.
- **Los diez casos de A3 salen de tres parches buenos**, uno por cada par de proyecto y frontera
  que permite el conjunto: python-semver en `function`, python-semver en `cli` y mdformat en
  `cli`, con siete parches malos derivados de ellos entre las tres etiquetas del criterio de
  salida.

## Base

Medido el 2026-11-15, ejecutando el orden, los candidatos y la regla de un testigo del arnés sobre
los 25 primeros candidatos de cada proyecto (mdformat paró en 16, en el límite de tiempo de la
sesión que midió), con pytest 8.3.4 en un entorno local en lugar de un contenedor:

| Proyecto | Candidatos mirados | Testigos |
|---|---|---|
| cachetools | 25 | 14 |
| python-semver | 25 | 18 |
| mdformat | 16 | 7 |

El test de esta medida llega con el script, en el ámbito `corpus`.

Leído en el cambio de cada uno de los seis primeros testigos: uno es una refactorización de 490
líneas, uno cambia las herramientas de los tests, y tres arreglan un comportamiento al que un
contrato de la primera versión no llega (un objeto con `__index__`, una clase pasada como
argumento, un plugin instalado). Solo encaja python-semver `0bd62d4`, a través de la función del
módulo `semver.replace`.

Ejecutado, para los tres pares: python-semver `0bd62d4` en `function`, python-semver `4e09ef0` en
`cli` con `python -m semver nextver`, y mdformat `27e2ba3` en `cli` con `python -m mdformat -`. Para
cada parche bueno, ejecutado sobre su base, los ejemplos de cambio fallan en la base y pasan con
el arreglo, y ningún test que pasaba en la base deja de pasar (511, 354 y 4.267 tests). Los siete
parches malos pasan los ejemplos o rompen tests exactamente como dice su etiqueta. Con solo el
cambio bajo `src/`, el parche bueno de `nextver` rompía un doctest de `docs/` que el commit
actualizaba, y el arnés habría rechazado un parche bueno; por eso el parche bueno toma todo lo que
está fuera de los tests.

Leído, no ejecutado: la proporción de testigos que caben en cada proyecto. En python-semver la
mayoría de los testigos llegan a una función del módulo o a la orden `pysemver`; en cachetools casi
todos son decoradores y métodos de clases, a los que no llega una función llamada con valores de
JSON; en mdformat al menos dos llegan a la orden `mdformat`.

Razonamiento, sin test: que la proporción de arreglos reales que caben en una frontera depende del
estilo de una biblioteca más que de que la biblioteca sea pequeña.

## Alternativas consideradas

- **Ampliar la frontera `function` para construir objetos y llamar a métodos.** Dejaría entrar a
  cachetools, y cambia el formato del contrato y la ADR-0039. Se decide cuando la proporción de
  arreglos que no caben, medida en todo el conjunto, diga que hace falta; no para llegar a los diez
  casos de A3.
- **Dejar que la autocomprobación pase del segundo testigo.** Haría más lenta cada autocomprobación
  para encontrar casos del conjunto, que es otro trabajo.
- **Elegir los casos a mano en la historia.** Devuelve la elección que tomarlos de los testigos
  quería quitar.
- **Tomar como parche bueno solo el cambio de código.** Un commit que actualiza su documentación
  con el arreglo daría un parche bueno que rompe un doctest.

## Consecuencias

- La hipótesis de que la mayoría de los requisitos reales caben como ejemplos en una frontera,
  confirmada en A0 sobre cambios elegidos a mano, se mide otra vez sobre cambios tomados de la
  historia; los resultados publicados dan los dos números.
- cachetools no da ningún caso a A3. Su pack sigue ejecutándose en el job `corpus`.
- El script que encuentra los testigos se mantiene con los casos, y sus resultados se guardan para
  que la elección se pueda repetir.
- La nota del cierre del bloque A en el roadmap da la proporción de arreglos que no caben.
