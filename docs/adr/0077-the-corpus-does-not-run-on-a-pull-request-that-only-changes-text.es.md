<!-- translation-of: 0077-the-corpus-does-not-run-on-a-pull-request-that-only-changes-text.md sha256:66a95b2fef5ff0b2 -->
# ADR-0077 · El corpus no se ejecuta en una pull request que solo cambia texto

**Estado:** aceptada

## Contexto

La [ADR-0052](0052-the-corpus-runs-in-ci-in-a-job-of-its-own-with-the-network.es.md) ejecuta los
tests del corpus en un job de CI propio, `corpus`, en cada pull request y en cada push a `main`, y
lo hace puerta. El job es el más largo de la CI: 722 segundos en la ejecución de #199, mientras que
el siguiente, `lint, types and tests`, tardó 365. Cinco jobs de `ci` son checks obligatorios de la
rama `main`, `corpus` entre ellos.

Muchas pull requests solo cambian texto: de las 40 últimas fusionadas, de #159 a #198, nueve solo
cambiaron ficheros Markdown bajo `docs/` fuera de `docs/requirements/` (#162, #174, #175, #180,
#182, #183, #189, #194 y #195), como una nota de la hoja de ruta o una ADR. Ningún test de
`tests/corpus` ni `tools/check_corpus.py` lee un fichero de `docs/`, así que un cambio así no puede
romper el corpus; aun así, cada una lo espera.

Un check obligatorio que no se ejecuta bloquea la fusión: cuando un filtro de rutas salta un
workflow, sus checks se quedan pendientes, mientras que un job o un paso saltado por una condición
informa de éxito.

## Decisión

Esto enmienda la ADR-0052 en cuándo ejecuta sus tests el job `corpus`; el resto se mantiene.

**En una pull request que solo cambia texto, el job `corpus` no ejecuta los tests del corpus.** Se
decide dentro del job:

- **Qué es texto es una lista cerrada:** un fichero cuyo nombre acaba en `.md` bajo `docs/`, salvo
  bajo `docs/requirements/`. Cualquier otro fichero, de `src/`, `tests/`, `tools/`, `.github/` o de
  cualquier otra ruta, ejecuta el job entero.
- **Un primer paso del job lista los ficheros cambiados** con `git diff --name-only --no-renames`
  contra la base de la pull request, con todo el historial, para que un fichero movido muestre sus
  dos rutas; los pasos del corpus se ejecutan con una condición sobre su salida.
- **Si el paso no puede decidir**, porque no se puede leer el diff o no se encuentra la base, el job
  se ejecuta entero o falla; nunca se salta. El paso está en el mismo job, no en un job propio del
  que dependa `corpus`.
- **Solo en `pull_request`.** En un push a `main` el job se ejecuta entero, para que un fallo del
  corpus se vea cuando el cambio se fusiona.
- **El resumen del job lo dice**: «el corpus no se ejecutó: la pull request solo cambia texto», con
  la lista de los ficheros.

Los demás jobs de la CI, las comprobaciones de gobernanza y los tests entre ellos, se ejecutan
siempre.

## Base

Medido en este repositorio: las duraciones de los jobs de la ejecución de `ci` de #199, y los
ficheros de las 40 últimas pull requests fusionadas, leídos con `gh`.

Comprobado en la documentación de GitHub
([troubleshooting required status checks](https://docs.github.com/en/pull-requests/how-tos/merge-and-close-pull-requests/troubleshooting-required-status-checks)):
un workflow saltado por un filtro de rutas, de ramas o por el mensaje de un commit deja sus checks
pendientes y bloquea la fusión; un job saltado por una condición informa de éxito; y un job que
depende de un job que falló se salta, así que puede no bloquear la fusión. Esto último es por lo
que el paso está en el mismo job. Una
[discusión de la comunidad de GitHub](https://github.com/orgs/community/discussions/44490) sigue
pidiendo filtros de rutas que funcionen con checks obligatorios.

Solo razonamiento: que `git diff --name-only` sin `--no-renames` nombra solo la ruta nueva de un
fichero renombrado, de modo que mover un test a `docs/` parecería texto, se sigue de cómo git
detecta los renombrados, y lo comprueba un test del paso cuando se construya.

## Alternativas consideradas

- **`paths-ignore` en el workflow.** Descartada: el workflow no se ejecutaría, y el check obligatorio
  `corpus` se quedaría pendiente y bloquearía la fusión de cada pull request de texto.
- **Un job propio que decide, del que depende `corpus`.** Descartada: si ese job fallara, `corpus` se
  saltaría e informaría de éxito, así que el corpus no se ejecutaría y el check estaría en verde.
- **Un segundo workflow con el mismo nombre que siempre tiene éxito**, la solución antigua de
  GitHub. Descartada: dos definiciones de un mismo check obligatorio, que pueden separarse.
- **Saltarlo también en un push a `main`.** Descartada: un fallo solo se vería en la siguiente pull
  request que ejecute el corpus.
- **Seguir ejecutándolo siempre.** Descartada: unos 12 minutos de runner y 6 de espera por cada pull
  request de texto, nueve de las cuarenta últimas, sin ninguna comprobación que el texto pueda
  hacer fallar.

## Consecuencias

- **Lo que se gana:** en una pull request de texto, unos 6 minutos de espera, porque
  `lint, types and tests` pasa a ser el job más largo, y unos 12 minutos de runner; nueve de las
  cuarenta últimas pull requests.
- **Lo que se arriesga:** un fallo del corpus que no viene del cambio, de la red o de un proyecto
  del corpus, no se ve en una pull request de texto; se ve en el push a `main` cuando se fusiona.
  La concurrencia de la CI cancela una ejecución en curso de la misma referencia
  (`cancel-in-progress`), así que un push a `main` seguido enseguida de otro puede perder su
  ejecución, y el fallo se ve entonces en la ejecución del push siguiente.
- **La lista cerrada solo es segura mientras ningún test del corpus lea un fichero Markdown de
  `docs/`.** Un test falla si alguno empieza a hacerlo.
- **Con el reparto del job,** que decide su propia ADR tras tres mediciones, la condición va en cada
  job en que se divida el corpus.
- **Al aceptarse** esta ADR, la ADR-0052 se marca como enmendada por ella.
