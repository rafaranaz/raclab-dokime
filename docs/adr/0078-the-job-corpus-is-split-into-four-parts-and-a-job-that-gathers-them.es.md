<!-- translation-of: 0078-the-job-corpus-is-split-into-four-parts-and-a-job-that-gathers-them.md sha256:9b4ead904567cd1b -->
# ADR-0078 · El job corpus se reparte en cuatro trozos y un job que los reúne

**Estado:** propuesta

## Contexto

La [ADR-0052](0052-the-corpus-runs-in-ci-in-a-job-of-its-own-with-the-network.es.md) ejecuta todos
los tests del corpus en un job de CI, `corpus`, que es un check obligatorio de la rama `main`. Es el
job más largo de la CI, y crece con cada caso. Cuatro ejecuciones con `--durations=0`, en #197, dos
en #198 y en #199, dieron estos segundos de pytest por partes:

| Parte | #197 | #198 | #198, tras el rebase | #199 |
|---|---|---|---|---|
| La auditoría de los seis casos de mdformat | 284 | 283 | 378 | 286 |
| La reserva a mano de B0 | 159 | 159 | 204 | 160 |
| Las autocomprobaciones de los paquetes | 101 | 101 | 133 | 101 |
| La auditoría de los seis casos de python-semver | 85 | 85 | 107 | 86 |
| La ejecución sellada de B1 | 36 | 36 | 43 | 36 |
| Los testigos | 33 | 33 | 44 | 33 |
| **pytest, en total** | **700** | **703** | **911** | **699** |

Tres ejecuciones quedan a menos de 4 segundos entre sí; la cuarta es un 30 % más lenta en todas las
partes por igual, lo que apunta al runner y no a un test. Un caso de mdformat cuesta unos 47
segundos y uno de python-semver unos 14, así que los dieciocho casos que añade B3 llevarían solo la
auditoría de unos 6 minutos a unos 15.

## Decisión

Esto enmienda la ADR-0052 en cómo se ejecuta el job `corpus`; el resto se mantiene.

**Los tests del corpus se ejecutan en cuatro jobs a la vez, y un job llamado `corpus` los reúne:**

| Trozo | Qué ejecuta |
|---|---|
| a | la auditoría de los casos de mdformat |
| b | la auditoría de los casos de python-semver y de cachetools |
| c | la reserva a mano y la ejecución sellada |
| d | todos los demás tests del corpus |

- **Ningún test queda fuera.** El trozo d ejecuta el corpus entero con las selecciones de a, b y c
  deseleccionadas, así que un test que ninguno selecciona cae en d; es el complemento por
  construcción, no una lista. Un paso del job `corpus` lee los informes JUnit de los cuatro trozos
  y exige que el número de sus tests sea igual al número de tests del corpus recogidos en una sola
  colección; si no, falla.
- **El job `corpus` falla salvo que los cuatro trozos acaben en `success`.** Depende de ellos y se
  ejecuta con `if: always()`; un trozo saltado o cancelado lo hace fallar igual que uno que falla.
  Conserva el nombre del check obligatorio, así que las reglas de la rama no cambian.
- **Cada trozo ejecuta la condición de la
  [ADR-0077](0077-the-corpus-does-not-run-on-a-pull-request-that-only-changes-text.es.md)** como
  un paso propio: en una pull request de texto se saltan sus pasos, no el job, que acaba en
  `success`.
- **El informe JUnit de las autocomprobaciones queda en el trozo donde se ejecutan**, y
  `tools/check_corpus.py` lo lee allí. Cada trozo escribe su duración.
- **Cuándo se vuelve a partir un trozo.** Si un trozo pasa de 6 minutos de pytest en tres
  ejecuciones seguidas, se divide sin otra ADR, y la pull request que lo divide lo dice.

## Base

Medido en este repositorio: las duraciones de cada test del corpus en las cuatro ejecuciones de
arriba, leídas de los registros del job.

Comprobado en la documentación de GitHub
([troubleshooting required status checks](https://docs.github.com/en/pull-requests/how-tos/merge-and-close-pull-requests/troubleshooting-required-status-checks)):
un job que depende de un job que falló se salta, y un job saltado informa de éxito, así que un job
que reúne a otros tiene que ejecutarse con `always()` y comprobar él mismo sus resultados.

No comprobado, y a medir en la primera ejecución con el reparto: cuántos núcleos tiene el runner, y
cuánto añaden la preparación y el clonado a cada trozo; en #193 todos los pasos salvo pytest
tardaron menos de 15 segundos en total. Con ellos, se espera que la espera del corpus baje de unos
12 minutos a unos 5, el trozo más largo; eso es razonamiento hasta que se mida.

## Alternativas consideradas

- **pytest-xdist dentro del único job.** Descartada: conserva el nombre del job, pero los runners
  tienen pocos núcleos y el corpus ejecuta podman, donde dos ejecuciones a la vez ya han dado fallos
  intermitentes; no se midió.
- **Exigir cada trozo por su nombre en las reglas de la rama.** Descartada: las reglas cambiarían
  cada vez que cambie el reparto, y un trozo que quedara fuera de ellas no bloquearía una fusión.
- **Repartir los tests por sus duraciones con un plugin como pytest-split.** Descartada por ahora:
  reparte mejor, pero añade una dependencia y un fichero de duraciones que mantener al día.
- **Mantener un solo job.** Descartada: crece hasta unos 20 minutos con los casos de B3.

## Consecuencias

- **La espera del corpus** es la de su trozo más largo, unos 5 minutos hoy frente a unos 12, una vez
  medida; el tiempo de runner crece en la preparación y el clonado de tres jobs más.
- **El crecimiento cae en el trozo de cada proyecto**, y la regla de los 6 minutos vuelve a partir un
  trozo sin ADR.
- **La comprobación del recuento** detecta un test perdido o ejecutado dos veces por una selección
  equivocada; un test que no se recoge en absoluto queda fuera de su alcance, como hoy.
- **El job `corpus` ya no ejecuta ningún test**: un fallo se ve en el trozo que lo ejecutó, y
  `corpus` dice qué trozo no acabó en `success`.
- **Al aceptarse** esta ADR, la ADR-0052 se marca como enmendada por ella.
