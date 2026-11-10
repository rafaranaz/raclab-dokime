<!-- translation-of: 0012-examples-are-observations-at-a-boundary.md sha256:ff10df88e96a47aa -->
# ADR-0012 · Un ejemplo es una observación en una frontera, comparada fuera del proceso del sujeto

**Estado:** aceptada

## Contexto

Si el valor esperado de una comprobación oculta está en el mismo proceso que el código examinado,
ese código puede leerlo o hacer que la comparación salga bien. Dos de las cuatro técnicas de
trampa medidas (sobrecargar los operadores de comparación, guardar estado entre llamadas)
funcionan así.

## Decisión

- Un ejemplo es una lista de pasos en una frontera declarada: `function`, `cli` o `http`. Cada
  paso tiene una entrada y lo que se espera observar.
- El código examinado recibe **solo las entradas**. Devuelve una observación serializada en JSON.
  La comparación con el valor esperado ocurre en el arnés, fuera de la zona de verificación.
- La comparación es exacta, salvo un **catálogo cerrado** de comparadores (cualquier
  identificador, cualquier marca de tiempo, número aproximado, colección sin orden, contiene,
  patrón, referencia a un paso anterior). Los ejemplos no contienen código. El catálogo solo crece
  por ADR.
- Cada ejemplo corre en un proceso nuevo.

## Base

Razonamiento, guiado por las técnicas clasificadas en
[ImpossibleBench](https://arxiv.org/abs/2510.20270). No se encontró ningún estudio que mida este
diseño.

## Alternativas consideradas

- **Tests ocultos montados en solo lectura junto al código examinado.** El código puede leerlos
  mientras se le examina.
- **Tests generados por un modelo a partir de los ejemplos.** El paso del ejemplo aprobado a la
  comprobación lo escribiría un modelo.

## Consecuencias

- El núcleo compara JSON y no sabe de lenguajes. `cli` y `http` no necesitan nada por lenguaje;
  `function` necesita una sonda pequeña en el pack del lenguaje.
- No expresa interfaces gráficas, concurrencia ni rendimiento.
- Los comparadores y las referencias entre pasos son un pequeño lenguaje dentro de los ficheros.
  Solo son aceptables mientras el catálogo esté cerrado.
