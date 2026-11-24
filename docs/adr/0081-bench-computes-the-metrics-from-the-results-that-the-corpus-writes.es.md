<!-- translation-of: 0081-bench-computes-the-metrics-from-the-results-that-the-corpus-writes.md sha256:4813475efaf4a7e5 -->
# ADR-0081 · bench calcula las métricas de los resultados que escribe el corpus

**Estado:** aceptada

## Contexto

La [ADR-0030](0030-the-harness-is-measured-on-a-corpus-with-known-verdicts.es.md) da al módulo
`bench` dos tareas: «ejecuta el arnés en modo auditoría» sobre los casos del corpus, y calcula las
métricas. Desde el bloque A las auditorías se ejecutan en otro sitio:
`tests/corpus/test_corpus_audit.py` audita cada caso con la orden `audit`, el git y el podman reales,
en el trabajo `corpus` de CI, partido en seis trozos
([ADR-0078](0078-the-job-corpus-is-split-into-four-parts-and-a-job-that-gathers-them.es.md)); en la
ejecución de `main` sobre `00419bc` los seis trozos tardaron entre 205 y 417 segundos de pytest cada
uno. La ejecución con la clave de los casos con un lote sellado solo la puede lanzar el mantenedor,
en su máquina, y la registra `tests/corpus/held-out-run.toml`.

Lo que dio una auditoría hoy es solo una línea del registro del trabajo, `case …: verdict …`. Nada
que un programa pueda leer lo guarda.

## Decisión

Esto modifica la ADR-0030 en quién ejecuta las auditorías; el resto se mantiene.

- **El test del corpus ejecuta las auditorías** y escribe, por cada caso que audita, una línea de
  JSON en un fichero de resultados: la clave del caso, su veredicto, su primera puerta que falla y
  si se dio la clave. Cada fichero registra el commit del repositorio en que corrió. El trabajo
  `corpus` guarda los ficheros de sus trozos como artefacto.
- **`bench` solo calcula.** Lee uno o más ficheros de resultados, con los datos del corpus en el
  repositorio: las etiquetas de los casos, `withdrawn.toml`, la lectura a ciegas de B3a,
  `witnesses.toml` y `held-out-run.toml`. No ejecuta ninguna auditoría, y no necesita ni la red ni
  podman. Se niega a comparar para la estabilidad dos ficheros que corrieron en commits distintos.
- **Cada cuenta dice si la ejecución tenía la clave.** Sin ella, un caso etiquetado
  `fails-a-held-out-example` pasa por diseño; para esa etiqueta, el valor de la reserva da las dos
  cifras, sin la clave y con ella.

## Fundamento

Razonamiento, sobre lo que midió este repositorio: los tiempos de los trozos del trabajo `corpus`, y
que la ejecución con la clave necesita al mantenedor. Ejecutar otra vez las auditorías dentro de
`bench` duplicaría ese tiempo para los mismos veredictos, y no podría ejecutar con la clave los casos
con un lote sellado en CI, donde la clave no está
([ADR-0073](0073-the-key-of-the-hold-out-lives-outside-ci-until-b4.es.md)). Calcular sobre ficheros
que escribe la ejecución es lo que hace del cálculo un test propio, sin red.

## Alternativas consideradas

- **`bench` ejecuta las auditorías, como dice la ADR-0030.** Descartada: duplica el test del
  corpus, que tiene que ejecutarse en CI de todos modos como su puerta, y duplica su tiempo.
- **`bench` lee los registros de CI.** Descartada: un registro es texto para una persona, su formato
  no es un contrato, y leerlo necesita la API de GitHub.
- **El test del corpus calcula él mismo las métricas.** Descartada: el test juzga cada caso frente a
  su veredicto esperado; las métricas necesitan todos los casos de una ejecución, dos ejecuciones
  para la estabilidad, y la ejecución con la clave, que ningún test por sí solo ve.

## Consecuencias

- `bench` es barato y se prueba sin red; la estabilidad necesita dos ficheros de resultados del
  mismo commit, lo que obliga a ejecutar otra vez el trabajo `corpus`.
- El formato del fichero de resultados, incluido el commit en que corrió, es un contrato entre el
  test del corpus y `bench`, y cambia en los dos a la vez.
- Un artefacto de CI caduca, así que los ficheros de resultados en los que se apoyan las cifras de
  una versión tienen que guardarse con esa versión.
- Los minutos de una persona por cambio, una métrica de la ADR-0030, no los calcula B3e.
