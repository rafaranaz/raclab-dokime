<!-- translation-of: ROADMAP.md sha256:eb69286c23522448 -->
# Hoja de ruta

*Read in [English](ROADMAP.md).*

Cada fase tiene criterios de salida. **La siguiente fase no se abre hasta que la anterior los
cumple todos** ([ADR-0003](adr/0003-rules-enforced-in-ci.es.md)). Si un criterio resulta imposible
o equivocado, se cambia aquí en un PR propio y con su razón, no se salta.

## Fase 0 · Forma de trabajo y puertas — terminada

Reglas de trabajo, pipeline de CI y skills de desarrollo, sin código del harness.

Criterios de salida:

- [x] Entorno reproducible: Python fijado, dependencias en `uv.lock`, instalación con `--locked`.
- [x] Puertas de calidad, gobierno, disciplina y auditoría en CI, cada una con requisitos EARS y
  tests ([docs/requirements/repo.md](requirements/repo.md)).
- [x] Forma de trabajo documentada en [CONTRIBUTING.es.md](../CONTRIBUTING.es.md).
- [x] ADR de las decisiones de proceso.
- [x] Skills de desarrollo en `.claude/skills/`.
- [x] Documentación en inglés y en español, con las traducciones comprobadas en CI.
- [x] CI en verde sobre el PR de la fase en GitHub.
- [x] Protección de `main` aplicada en GitHub (ver abajo).

## Fase 1 · Arquitectura de referencia — completada

La arquitectura del producto, decidida con evidencia. Cada decisión es un ADR que dice en qué se
apoya (literatura, razonamiento o una prueba) y las alternativas consideradas
([ADR-0008](adr/0008-built-new-nothing-is-ported.es.md)). Se entrega en hitos, cada uno un pull
request revisable por separado:

| Hito | Qué entrega | Ámbito |
|---|---|---|
| 1.1 Mapa y decisiones | Qué es el producto y qué afirma, los invariantes, el contexto, las zonas de confianza, los módulos con sus dependencias permitidas, y los ADR 0008 a 0032 | `arch` |
| 1.2 Gobierno alineado | Una comprobación de que cada ADR desde el 0008 dice en qué se apoya; el acuerdo de trabajo alineado con los bloques de la fase 2 | `repo` |
| 1.3 Datos y evidencia | Los formatos del contrato y de los ejemplos, el predicado de la evidencia, el registro y la secuencia de extremo a extremo de un cambio | `arch` |
| 1.4 Estados y flujos | El esquema del fichero de flujo, los estados, las puertas, los presupuestos, la composición por modo y las reglas del validador | `arch` |
| 1.5 Contratos de importación | Las reglas de dependencia del mapa de módulos, comprobadas en CI (import-linter) | `repo` |
| 1.6 Fase cerrada | Criterios de salida marcados e hipótesis listadas con su prueba y su bloque | `arch` |

Datos y evidencia va antes que estados y flujos porque el bloque A depende de los formatos,
mientras que el fichero de flujo no se usa hasta el bloque C. Cada módulo recibe sus requisitos
EARS de alto nivel cuando se abre su ámbito en la fase 2.

Antes de aceptarse, las decisiones se comprobaron contra los diez invariantes por tres vías
independientes. Las correcciones, un glosario y los ADR 0033 a 0035 salieron de esa comprobación y
de poner por escrito los formatos.

Criterios de salida:

- [x] Los documentos anteriores están en `docs/architecture/` y sus diagramas pasan la validación.
- [x] Cada ADR desde el 0008 está aceptado o queda expresamente como hipótesis con su prueba.
- [x] La comprobación de que cada ADR dice en qué se apoya y los contratos de importación están en
  CI.
- [x] La arquitectura está aprobada en revisión.

## Fase 2 · Construcción por bloques

Siete bloques, cada uno con algo que una persona puede usar y una versión publicada
([ADR-0029](adr/0029-build-order-starts-with-auditing.es.md)). Dentro de un bloque hay un solo
ámbito de módulo abierto a la vez, en el orden indicado. Un bloque se cierra cuando su criterio de
salida, medido sobre el conjunto de casos
([ADR-0030](adr/0030-the-harness-is-measured-on-a-corpus-with-known-verdicts.es.md)), se cumple y
se publica. Un resultado malo también se publica.

| Bloque | Qué puede hacer un usuario al cerrarlo | Módulos, en orden | Criterio de salida | Versión |
|---|---|---|---|---|
| A · Auditar | Verificar un cambio terminado, hecho por cualquier agente, contra un contrato escrito a mano, en local y en CI | `core`, `contract`, `packs`, `sandbox` (entorno de verificación), `platform` (repositorio del proyecto, almacenes y reloj), `verify`, `evidence`, `interfaces` | Ningún falso aprobado en parches que fallan ejemplos visibles, modifican tests o rompen tests existentes | 0.1 |
| B · Reservar | Lo mismo, con ejemplos que el agente no ha visto | `oracle`, `platform` (almacén de lo sellado), `verify`, `bench` | Ningún falso aprobado en las cuatro técnicas de trampa; valor de la reserva medido | 0.2 |
| C · Lanzar | Dar la tarea al arnés y que dirija al agente hasta que el cambio pasa o pregunta | `sandbox` (trabajo), `agents`, `engine` | El mismo cambio completa el circuito con dos perfiles de agente, uno con un modelo de pesos abiertos | 0.3 |
| D · Proteger | Saber qué daña el cambio fuera de lo pedido | `verify` | Las regresiones inyectadas en código cubierto se detectan; tasa de preguntas medida | 0.4 |
| E · Atestar | Entregar evidencia firmada que un tercero verifica sin el arnés | `platform` (firma y forja), `evidence`, `delivery` | Alguien sin el arnés instalado verifica un fichero de evidencia | 0.5 |
| F · Especificar | Escribir el contrato con ayuda, en español o en inglés | `gateway`, `spec` | Minutos de persona por contrato medidos; prueba de atención hecha | 0.6 |
| G · Generalizar | Usarlo con un segundo lenguaje, con más agentes y en equipo | `packs`, `agents`, `delivery` | El conjunto de casos incluye un repositorio Java; tres agentes distintos completan el circuito | 1.0 |

Los hitos de un bloque se escriben aquí cuando el bloque se abre, y sus números medidos cuando se
cierra. El orden de los bloques B y C se confirmó al cerrar el bloque A: B antes que C, porque el
bucle de C devuelve los fallos al agente hasta que el cambio pasa, y la reserva es la defensa contra
el sobreajuste a los ejemplos visibles
([ADR-0029](adr/0029-build-order-starts-with-auditing.es.md)).

**El bloque A se cerró el 2026-11-18**, con la versión 0.1.0; su
[nota de cierre](#bloque-a--nota-de-cierre) está tras sus hitos. Su primer hito, A0, no tuvo código:
probó a mano los formatos de los que depende el resto del bloque.

**A0 está hecho.** Se hicieron tres contratos a mano sobre cambios que proyectos públicos ya habían
hecho (un limpiador de descripciones de pull request, `humanize.naturalsize` y el escapado de
barras verticales en `tabulate`), y cada uno se comprobó ejecutando sus ejemplos contra el código
antes y después del cambio. Los nueve requisitos caben como ejemplos en una frontera. La persona
los aprobó. La lectura llevó unos 4 o 5 minutos en el limpiador de descripciones, unos 2 en
`naturalsize` y unos 3 en `tabulate`, cuyos formatos la persona no conocía; son estimaciones de la
propia persona, no mediciones. Lo que cambió en el formato está en
[el contrato](architecture/03-data-and-evidence.es.md#el-contrato). Los tres
repositorios del corpus son otros, para que lo que se sabe de los proyectos de A0 no se filtre en
las pruebas: [cachetools](https://github.com/tkem/cachetools) (MIT),
[python-semver](https://github.com/python-semver/python-semver) (BSD-3-Clause) y
[mdformat](https://github.com/executablebooks/mdformat) (MIT). Los tres son Python puro, se
instalan en Python 3.13 y sus suites pasan en menos de 15 segundos (416, 512 y 4286 tests); dos
tienen frontera de línea de órdenes (`pysemver`, `mdformat`) y todos tienen frontera de función.
Tienen 72, 25 y 38 commits con "fix" en el mensaje que tocan tests, que es una cuenta de
candidatos, no de casos utilizables.

**A1 está hecho.** `dokime contract check` valida un fichero de contrato y dice qué le falta, con una
línea por hallazgo y un código de salida por veredicto
([ADR-0040](adr/0040-commands-exit-with-a-code-for-each-verdict.es.md)). Se construyó en tres
módulos: `core` (veredictos, hallazgos y el lector estricto del
[ADR-0037](adr/0037-a-contract-is-read-by-strict-rules-of-its-own.es.md)), `contract` (la
comprobación) e `interfaces` (la orden). Los tres contratos de A0, reescritos con las reglas que
fijó A1, pasan sin ningún hallazgo. Su criterio de salida se cumple: con un texto que no es EARS,
un requisito sin ejemplo, un duplicado y una contradicción sembrados en uno de ellos, la orden
informa de los cuatro en una ejecución. Los defectos de lectura (una clave repetida, un valor cuyo
tipo depende del lector, un texto en varias líneas) se informan igual. Lo que A1 no hace: no
ejecuta nada, así que un contrato que pasa todavía no dice nada del código.

Cómo usa el corpus esos repositorios:

- **Referenciar, no copiar.** Un caso apunta a `repositorio@commit`; no se copia código de esos
  proyectos a este repositorio. Si alguna vez se copia algo, el aviso de copyright y el texto de la
  licencia viajan con ello.
- **No tocar nunca los originales.** Las ejecuciones se hacen sobre copias locales. No se abre
  ninguna pull request, issue ni comentario en esos proyectos.
- **Nombrarlos en cada informe**, con la versión, para que los números se puedan reproducir.

### Hipótesis

Algunas decisiones se apoyan en razonamiento. Cada una tiene una prueba que se hace antes del
bloque que depende de ella, y no se construye sobre una hipótesis fallida sin una decisión nueva.
La lista completa está en el [índice de arquitectura](architecture/README.es.md#hipótesis-por-probar).

| Hipótesis | Prueba | Si falla |
|---|---|---|
| La mayoría de los requisitos reales se pueden expresar como ejemplos en una frontera | A mano, antes de cualquier código del bloque A. **Medida** al cerrar el bloque A: se cumple en los cambios elegidos a mano de A0, 9 de 9 requisitos; en los arreglos sacados de la historia, son expresables entre 15 y 20 de 41 ([nota de cierre](#bloque-a--nota-de-cierre)) | Se revisa el formato del contrato antes de construir; si se amplía la frontera `function` va a la revisión estratégica |
| Aprobar dos o más ejemplos por caso cuesta un tiempo aceptable | A mano, junto con la anterior | Se revisa la regla de reserva |
| ~~Un pack se puede proponer a partir de la configuración de CI de un proyecto~~ | **Descartada** por la [ADR-0041](adr/0041-the-environment-of-a-verified-project-is-a-dockerfile.es.md): el arnés no deduce un pack, lo escribe una persona | Aplicado: los packs se escriben a mano por proyecto, un coste de adopción |
| La reserva por caso detecta soluciones sobreajustadas | La métrica "valor de la reserva" al cerrar el bloque B | La reserva pasa a ser opcional y el peso va a las relaciones y al bloque D |
| Un agente arranca con su credencial y un directorio de configuración hecho para la ejecución | Dos agentes en Linux y macOS, antes del bloque C | El arnés usa la configuración normal del agente y la evidencia lo dice |
| Un modelo de pesos abiertos completa el circuito | Al cerrar el bloque C | Se publica con qué modelos funciona; la versión no se bloquea |
| Una persona detecta un ejemplo erróneo plantado entre los propuestos | Al cerrar el bloque F | Cambia la forma de presentar los ejemplos antes de cerrar el bloque F |

### Bloque A · Hitos

| Hito | Qué se puede enseñar | Módulos | Se cierra cuando |
|---|---|---|---|
| A0 Pruebas a mano | Tres cambios reales con un contrato escrito a mano y aprobado por una persona, cronometrado; tres repositorios elegidos para el conjunto de casos | Ninguno | Se conocen la proporción de requisitos que caben como ejemplos y los minutos por contrato, y el formato se confirma o se revisa |
| A1 Contrato comprobable | Una orden que valida un contrato y dice qué le falta | `core`, `contract`, `interfaces` (solo la orden) | Detecta todos los defectos sembrados en contratos de prueba: sintaxis, ejemplos contradictorios, duplicados, requisitos sin ejemplo |
| A2 Entorno reproducible | Una orden que construye la imagen de un proyecto desde su pack y comprueba el pack con la historia del proyecto | `packs`, `sandbox`, `platform` (solo el repositorio del proyecto), `interfaces` (solo la orden) | Los packs de los tres repositorios se construyen y pasan su autocomprobación |
| A3 Auditoría | Una orden que audita un cambio: línea base, rutas protegidas, ejemplos visibles en las fronteras `cli` y `function`, tests existentes, un veredicto agregado y un fichero de evidencia; el directorio del cambio (`.dokime/changes/<story>/`) y el registro de eventos con hashes encadenados, planeados para A1 y no construidos | `core`, `corpus`, `platform`, `packs`, `oracle` (solo comparar), `verify`, `evidence`, `interfaces` | El criterio de salida del bloque, sobre los diez primeros casos del conjunto, etiquetados antes de ejecutarlos |
| A4 Auditoría en CI | Un flujo que audita un pull request y adjunta la evidencia, activado en este repositorio; versión 0.1 | `interfaces` | Un pull request real de este repositorio lleva su evidencia |

`interfaces` se abre tres veces en el bloque A: en A1 para la orden `contract check`, que solo lee
el fichero, llama a `contract` y muestra sus hallazgos; en A2 para la orden que construye una imagen
y comprueba un pack, que lee el pack y llama a `packs`; y en A3 para `audit`. `platform` se abre dos
veces: en A2 para el adaptador del repositorio del proyecto
([ADR-0042](adr/0042-a-port-of-the-project-repository-composes-the-trees-that-are-built.es.md)), y
en A3 para los almacenes y el reloj. Los ámbitos de un módulo
se abren por incrementos, como `core`
([ADR-0036](adr/0036-a-milestone-may-open-an-increment-of-a-later-module.es.md)).

A3 abre sus ámbitos en este orden, cada uno después de los que necesita:

1. `core`: el directorio del cambio, el registro con hashes encadenados y la lectura de la
   política ([ADR-0054](adr/0054-the-policy-is-an-optional-file-of-values.es.md)), que usan todos
   los demás ámbitos.
2. `corpus`, una primera vez: los diez casos con sus etiquetas y la puerta de las etiquetas. La
   etiqueta de un caso queda fijada en `main` antes de que el arnés vea
   el caso ([ADR-0055](adr/0055-a-case-of-the-corpus-is-labelled-by-how-it-is-built.es.md)), así
   que las puertas no se construyen con los casos delante y sin fijar.
3. `platform`: los almacenes y el reloj, `compose_with_patch`, que rechaza una ruta con una parte
   `.git` en mayúsculas o minúsculas, y la composición sobre un árbol de la
   [ADR-0058](adr/0058-existing-tests-runs-the-tests-of-the-base-on-the-code-of-the-patch.es.md).
4. `packs`: `tests.config`, las secciones de los ficheros mixtos y la regla de los candidatos
   (ADR-0056, ADR-0059, ADR-0060), que lee `verify`.
5. Una ADR sobre el programa que ejecuta un ejemplo en su frontera dentro de la zona de
   verificación, antes de los módulos que usan sus observaciones: la ADR-0063.
6. `core`, un incremento: el tipo de una observación y el puerto que observa, aparte del puerto del
   entorno de verificación, que lee `oracle` e implementa `sandbox` (ADR-0063).
7. `oracle`: comparar observaciones con lo esperado; separar los ejemplos visibles de los sellados
   sigue en el bloque B.
8. `sandbox`: el programa que observa los ejemplos dentro de la zona y el adaptador de podman del
   puerto (ADR-0063).
9. `verify`: `baseline`, `protected-paths`, `visible-examples`, `existing-tests` y la agregación.
   Un parche puede traer un enlace simbólico que apunte fuera del árbol, así que lo que lea un
   fichero del árbol extraído en la máquina de la persona lo abre sin seguir enlaces, como el
   lector del informe (ADR-0045). El doble del puerto del repositorio auditado que escriba
   `verify` se prueba contra CORE-099, que dice que la composición sobre un árbol sustituye su
   región: un doble que la superpusiera haría pasar tests de `verify` que deberían fallar.
10. `evidence`: el fichero de evidencia, sin firmas, que son del bloque E.
11. `interfaces`: la orden `audit`, que abre el contrato del directorio del cambio, y cualquier
    otro fichero del árbol, sin seguir enlaces, por la misma razón.
12. `corpus`, una segunda vez: una pull request de `repo` que da al job `corpus` los clones que
    necesita además de las autocomprobaciones; el script de los testigos (ADR-0057) y
    `git apply --check` de cada parche sobre su base; la auditoría ejecutada sobre los diez casos; y
    el criterio de salida medido. Los clones hacen falta aquí de todos modos, y nada entre las dos
    pasadas depende de ellos.

A2 se construye primero como el camino más delgado que funciona, `dokime env check` sobre cachetools
detrás de los puertos, y después se endurece una pieza cada vez, cada una con su requisito y su
test. El esqueleto fue en este orden, y está terminado:

1. `core`: el resultado de una ejecución, su informe y los límites de su lector; el puerto del
   entorno de verificación.
2. `platform`: el adaptador de git con la historia, el cambio de un commit, la composición con las
   rutas de otro commit y la extracción, con los rechazos de la ADR-0042. La composición con un
   parche se rechaza con `patch-not-supported` hasta A3.
3. `sandbox`: el adaptador de podman, que construye, ejecuta con las cuatro garantías de la ADR-0043
   y lee el informe con su límite de tamaño y rechazando un `DOCTYPE`. Los tests de las garantías se
   ejecutan en CI.
4. `packs`: la regla de orden de la ADR-0044 y el bucle de la autocomprobación sobre los puertos.
5. `interfaces`: la orden `dokime env check`.
6. Ejecutarla sobre cachetools. Dos testigos entre los diez primeros candidatos significan que el
   esqueleto camina.

El esqueleto caminó el 2026-11-15, con git 2.47.3 y podman 5.4.2, sobre los tres repositorios del
conjunto de casos, cada uno con un pack escrito para él:

| Proyecto | Commit | Candidatos mirados | Testigos | Tiempo | Restos |
|---|---|---|---|---|---|
| cachetools | `1ce79ef` | 3 | 2 | 21 s | ninguno |
| python-semver | `b6e83e3` | 3 | 2 | 37 s | ninguno |
| mdformat | `56b24ef` | 6 | 2 | 254 s | ninguno |

La imagen `python:3.13-slim` ya estaba en el almacén; los tiempos con el almacén vacío no se
midieron. Un SIGTERM a mitad de una ejecución de cachetools, enviado a `python -m dokime.interfaces`,
a la orden `dokime` instalada y a `uv run dokime`, no dejó ningún contenedor ni ningún directorio
temporal; `uv run` reenvía la señal y termina con 143.

**A2 se cerró el 2026-11-15**, con su criterio de salida y no con todo el endurecimiento. Además del
esqueleto llevó dos piezas más:

1. Los packs de los tres repositorios en `tests/corpus/`, fijados por digest y versiones exactas,
   ejecutados contra cada proyecto en su commit, que no se copia, en un job `corpus` de CI que
   falla salvo que cada proyecto se haya autocomprobado y haya pasado (ADR-0052).
2. Una línea por candidato según `env check` lo mira: mdformat había estado 254 s sin escribir
   nada entre los programas y el resultado.

Medido en el cierre, con los packs fijados:

| Proyecto | Testigos entre los candidatos | En la máquina de desarrollo, imágenes en el almacén | En el job `corpus`, un runner nuevo |
|---|---|---|---|
| cachetools | 2 de 3 | 16 s | 10 s |
| python-semver | 2 de 3 | 32 s | 12 s |
| mdformat | 2 de 6 | 248 s | 89 s |

El job `corpus` tardó 2 minutos en total. A2 resolvió la única hipótesis de la tabla de arriba cuya
prueba le tocaba, que un pack se puede proponer desde la configuración de CI de un proyecto: la
ADR-0041 la descartó por decisión, no por una prueba. La autocomprobación para en el segundo
testigo, así que ya no se mide cuántos testigos hay entre los diez primeros; la ADR-0044 daba 7, 8 y
4.

Apuntado como deuda, que no bloquea ningún hito:

- Un test con podman que se ejecuta hasta tres veces y exige `memory-limit` al menos una: hoy
  ningún test con un motor real lo exige, así que un podman o un conmon que dejara de informarlo
  pasaría sin verse.
- El adaptador de docker, para que los tests de las garantías se ejecuten con los dos motores.
- `--from` opcional, con un `head()` del adaptador de git.
- Una operación del puerto que dé el árbol de un commit, en vez de componer un commit consigo mismo,
  y una composición de rutas sobre un árbol, la base con el parche aplicado, que `existing-tests`
  necesita en A3 (ADR-0058); y un solo sitio para el tratamiento de SIGTERM, hoy copiado en
  `sandbox`, `packs` e `interfaces`.
- Opcional: `pip install --require-hashes` en los Dockerfile del conjunto de casos.
- Los testigos guardados para que la siguiente ejecución de una autocomprobación use los mismos,
  como dice la ADR-0041: no se construyó en A2.
- Un `at` del registro anterior al del evento previo no se detecta. El reloj del sistema puede
  retroceder de verdad, así que se decide cuando haya un caso.
- Un story, el nombre de un cambio y del `story` de su contrato, no tiene límite de longitud, y un
  sistema de ficheros admite 255 bytes por nombre; y `Fix` y `fix` serían un mismo directorio en un
  sistema de ficheros que no distingue mayúsculas, como macOS por defecto. Cambiar la regla cambia
  también la del contrato. El patrón de un nombre está además copiado de `core.layout` en
  `evidence`, que comprueba el story, los requisitos y los ejemplos inestables: cuando cambie la
  regla, `core` la expone y `evidence` la usa, para que las dos copias no se separen.
- De adopción: una imagen cuyo `USER` no es root. SANDBOX-038 la rechaza hoy, así que no es una
  protección contra código hostil sino la compatibilidad con imágenes que fijan un usuario, y
  ninguno de los tres packs la necesita. Se midieron cinco variantes con podman 5.4.2
  ([#81](https://github.com/rafaranaz/raclab-dokime/pull/81)): solo `--userns=keep-id:uid=U,gid=G`,
  con los números del usuario, deja que ese usuario lea sus propios ficheros y escriba en la salida
  con los ficheros a nombre de la persona; ahí no se acepta un nombre. La opción recomendada para
  cuando un usuario lo necesite lee esos números del `/etc/passwd` y el `/etc/group` de la imagen
  con `podman create` y `podman cp`, sin ejecutar nada; el código del proyecto puede reescribir esos
  ficheros durante la construcción, así que es una superficie nueva en A3 y necesita su decisión
  entonces.
- Un test de `no-new-privileges` con un programa setuid real, que depende del anterior: la imagen
  del corpus trae `su`, `passwd` y otros, y `passwd -S tester`, ejecutado por un usuario que no es
  root, muestra las fechas de `/etc/shadow` sin la opción y no las muestra con ella.

**A3 se cerró el 2026-11-18**, con su criterio de salida: `dokime audit` sobre los diez casos del
corpus, etiquetados y confirmados antes de que el arnés los ejecutara (ADR-0055), no da ningún falso
acepto.

Medido, con git 2.47.3 y podman 5.4.2, sobre los clones de los tres proyectos:

| Caso | Etiqueta | Veredicto | `expected` | Primera puerta con `FAIL` | `failing_gate` |
|---|---|---|---|---|---|
| mdformat/format-a-blank-paragraph-between-blocks | bueno | PASS | PASS | — | — |
| mdformat/fixes-only-a-code-block-before-the-blank | falla un ejemplo visible | FAIL | FAIL | visible-examples | visible-examples |
| mdformat/skips-the-html-check-and-edits-its-test | edita tests | FAIL | FAIL | protected-paths | protected-paths |
| mdformat/fix-with-a-regression-in-loose-lists | rompe tests existentes | FAIL | FAIL | existing-tests | existing-tests |
| python-semver/replace-keeps-the-constructor-error | bueno | PASS | PASS | — | — |
| python-semver/replace-fixes-only-major | falla un ejemplo visible | FAIL | FAIL | visible-examples | visible-examples |
| python-semver/replace-with-a-regression-in-bump-minor | rompe tests existentes | FAIL | FAIL | existing-tests | existing-tests |
| python-semver/nextver-bumps-build-only-versions | bueno | PASS | PASS | — | — |
| python-semver/nextver-fixes-only-patch | falla un ejemplo visible | FAIL | FAIL | visible-examples | visible-examples |
| python-semver/nextver-changes-the-tests-to-fit | edita tests | FAIL | FAIL | protected-paths | protected-paths |

- **Ningún falso acepto**: los siete parches malos fallan, cada uno primero en la puerta que nombra
  su etiqueta, y los tres buenos pasan ([#128](https://github.com/rafaranaz/raclab-dokime/pull/128)).
- **Los dos casos que editan tests los caza también `existing-tests`**, como midió a mano la
  ADR-0058 cuando eligió los tests de la base: con el cambio fallan tres tests de python-semver y uno
  de mdformat, además de `protected-paths`. Las dos puertas están en el estado `verifying`, que se
  ejecuta entero. La auditoría lo midió; ningún test lo exige todavía, aunque la ADR-0058 decía que
  su test llega con `corpus`.
- **El tiempo de las auditorías de los diez casos**: 361 s en la máquina de desarrollo, con las
  imágenes en el almacén; 275 s y 321 s para el mismo test en dos ejecuciones del job `corpus` de
  CI, donde el job ejecuta 135 tests, ninguno saltado, en unos cinco minutos.
- **La revisión de los casos** llevó 37 minutos de reloj, del mantenedor con la ayuda de otro modelo
  cuyas afirmaciones se comprobaron ejecutando el código (`tests/corpus/review.toml`, 2026-11-16).
- **Antes de ejecutar los casos**, cada parche se aplicó sobre su base con `git apply --check`, y
  los tres commits de los que salen los casos buenos fueron testigos con la regla del arnés sobre
  podman, poniendo en verde los tests de `tests/corpus/witnesses.toml`
  ([#127](https://github.com/rafaranaz/raclab-dokime/pull/127)).

Razonado, no medido:

- Diez casos muestran que las puertas de A3 cazan las tres formas de fallar que nombra el criterio
  de salida, en estos diez. No dicen cuántos otros parches pasarían; esa es la métrica del bloque B.
- Ningún caso del corpus acaba en `ASK`, así que la parada de la ejecución en un estado que pregunta
  solo se prueba con dobles.
- No se midió el tiempo de la revisión sin la ayuda de otro modelo; es el coste de adopción que
  pagaría una persona sin esa ayuda. El mantenedor decidió, al cerrar el bloque A, no estimarlo
  ([nota de cierre](#bloque-a--nota-de-cierre)).

A3 no resolvió ninguna hipótesis de la tabla de arriba; ninguna tenía su prueba en A3.

La proporción de arreglos reales que no caben en el formato del contrato, que pide la ADR-0057, se
mide en la [nota de cierre del bloque A](#bloque-a--nota-de-cierre).

Apuntado como deuda, que no bloquea ningún hito:

- Un test del corpus que exija que `existing-tests` falle en los dos casos que editan tests, la
  medida de la ADR-0058.
- Dos `raise` defensivos de `interfaces/audit.py` a los que no llega ningún camino público, y la
  orden `audit`, medida por la cobertura solo en el proceso: sus tests con los motores reales la
  ejecutan en un proceso propio, como los de `env check`.

Apuntado mientras se construye A4:

- **Un límite de A4: la evidencia de este repositorio no cubre los tests que necesitan git o
  podman.** Su pack ejecuta los tests en una imagen sin ellos, que instala solo lo que fija
  `uv.lock` (REPO-142); git por apt no se podría fijar así. De los 1883 tests, medido en la imagen
  sobre la base el 2026-11-18: pasan 1662; 131 necesitan git (88 errores, 27 fallos, 16 saltos); 63
  se saltan sin podman; 26 se saltan porque no se piden los tests del corpus; y 1 se salta porque
  el contenedor corre como root. Esos tests se siguen ejecutando en el job "lint, types and tests"
  de cada pull request: la auditoría se añade a esa CI, no la sustituye.
- **Deuda: los packs del corpus no ejecutan pytest con `--continue-on-collection-errors`**, como sí
  hace el de este repositorio (REPO-146). Sin ello, un módulo de tests que no se importa detiene
  todos los tests de un lado. Ninguno de los diez parches rompe una importación, así que sus
  resultados no cambian.

### Bloque A · Nota de cierre

**A4 se cerró el 2026-11-18, y con él el bloque A**, con la versión 0.1.0 y la etiqueta `v0.1.0`
([ADR-0068](adr/0068-the-harness-is-named-by-its-version-and-its-commit.es.md)).

**El criterio de salida de A4 lo cumple
[#146](https://github.com/rafaranaz/raclab-dokime/pull/146)**, la primera pull request de este
repositorio auditada en CI con el arnés de su base
([ADR-0071](adr/0071-the-harness-that-audits-a-pull-request-is-that-of-its-base.es.md)):

- Su contrato, el de la historia `show-the-version`, fue antes en una pull request propia,
  [#145](https://github.com/rafaranaz/raclab-dokime/pull/145), cuya fusión por el mantenedor fue su
  aprobación ([ADR-0067](adr/0067-a-person-approves-the-contract-before-a-change-is-audited-against-it.es.md)).
- La auditoría dio `PASS`, con las seis puertas de A3 y `repeatability` ejecutadas, `repeated` de 2
  ejecuciones y coherente, el commit del arnés el de la base, `b7b87e0`, y la evidencia
  `sha256:e9cb2094…` en el artefacto del job. El paso de la auditoría tardó 136 s en CI, y la misma
  auditoría 358 s en la máquina de desarrollo.
- La sesión que revisa el trabajo comprobó la evidencia de punta a punta contra git: su huella es
  la del registro del job, `read_back` no da hallazgos, las huellas del contrato, del parche y del
  árbol son las de la base, las de `git diff --binary` de la base a la cabeza y las de la cabeza, y
  la cadena del registro es íntegra, con la cabeza que cita la anterior a `evidence.built`, que
  registra la misma huella.
- En #146 el agente no tocó cinco tests que el contrato no autorizaba, que sustituyen la lectura de
  la versión, porque `protected-paths` habría rechazado el cambio: el contrato actuó antes de la
  auditoría, mientras se escribía el cambio.

**El criterio de salida del bloque A**, ningún falso aceptado en parches que fallan ejemplos
visibles, editan tests o rompen tests existentes, se midió en A3 sobre los diez casos del corpus, y
se cumple.

**La medida de la ADR-0057, la proporción de arreglos reales que caben en el contrato**
([#147](https://github.com/rafaranaz/raclab-dokime/pull/147), `tests/corpus/witnesses.toml`):

- **Los testigos**: 41, con los candidatos de la autocomprobación en podman desde el commit de cada
  proyecto: 14 de 25 candidatos en cachetools, 20 de 25 en python-semver y 7 de 16 en mdformat. La
  medida del 2026-11-15, en un entorno local, había encontrado 18 en python-semver en lugar de 20, y
  no apuntó los commits; la diferencia no se reconcilió.
- **Dos lecturas de cada testigo**, con los dos filtros de la ADR-0057, aislado y expresable en una
  frontera de la ADR-0039: la de la sesión que construye, y la de la sesión que revisa el trabajo,
  que los leyó antes de ver las primeras etiquetas. Coinciden en 33 de 41 en aislado (κ 0,57), 36
  en expresable (κ 0,75) y 38 en si caben, aislados y expresables (κ 0,84). Caben 12 de 41 en la
  primera lectura y 15 en la segunda; las tres diferencias van en el mismo sentido.
- **Una muestra ejecutada**: un testigo expresable y uno que no en cada proyecto, sorteados con la
  semilla 20261118 y ejecutados en la imagen del pack de su proyecto a los dos lados del cambio. Los
  seis confirman la lectura; en cachetools el único expresable salió por fuerza.
- **Lo que no cabe**: entre 26 y 29 de los 41 testigos, del 63 % al 71 %. El motivo principal es el
  mismo en los tres proyectos: el arreglo necesita un objeto, una clase, un método o un plugin
  instalado, a los que no llegan una función llamada con valores JSON ni una línea de órdenes.
  cachetools, cuyos arreglos son decoradores y métodos, da 0 o 1 de 14.
- **Expresables sin el filtro de aislado**: entre 15 y 20 de 41, porque la hipótesis de A0 habla de
  requisitos, y una funcionalidad nueva también lo es.
- **A0, en su unidad**: caben como ejemplos 9 de 9 requisitos, en tres cambios elegidos a mano.
  Midió requisitos en cambios elegidos; la ADR-0057 mide arreglos sacados de la historia. No se
  restan ni se comparan como si fueran lo mismo.
- **Un hallazgo: "aislado" no está bien definido en la ADR-0057.** La primera lectura lo tomó como
  "el cambio es un arreglo", así que una funcionalidad nueva o una deprecación no cuentan; la
  segunda, como "el cambio es solo el comportamiento buscado, sin refactorización ni herramientas".
  Esa es la causa de la mayoría de las diferencias en aislado.
- **Comparada con SWE-bench Verified solo como orden de magnitud**, porque son medidas distintas de
  cosas distintas. Allí, según leyó la sesión que revisa el trabajo en
  [el relato de OpenAI](https://openai.com/index/introducing-swe-bench-verified/), cada muestra la
  etiquetaron tres anotadores distintos que superaron unas pruebas de entrada, con una escala de
  gravedad de 0 a 3 para cada criterio; un 38,3 % de las muestras se marcaron por enunciados
  subespecificados y un 61,1 % por tests que podían rechazar soluciones válidas; se excluyó el
  68,3 %, y quedaron 500 muestras. Nuestra lectura usó dos lectores en lugar de tres, sin pruebas
  de entrada, con la muestra ejecutada como calibración.

**Lo que A3 dejó abierto, y una corrección:**

- El tiempo de la revisión sin la ayuda de otro modelo no se estima: el mantenedor decide que una
  estimación de memoria valdría poco. Si importa para la adopción, se mide con casos nuevos en el
  bloque B.
- La separación fina de los mensajes de los hallazgos no se hizo en A4, aunque la lista de lo que
  quedaba por decidir decía que sí:
  la [ADR-0069](adr/0069-the-predicate-v0-2-adds-what-a4-records.es.md) la dejó fuera, así que
  `message` está en el predicado v0.2 pero ningún módulo lo rellena, y el mensaje entero de un
  hallazgo sigue en `untrusted`. Se hace en cada módulo cuando se toque por otro motivo.

**Para la revisión estratégica del mantenedor**, que vive fuera del repositorio, al cerrar el
bloque A:

- Si el "aislado" de la ADR-0057 cuenta las funcionalidades nuevas.
- Si la frontera `function` se amplía a objetos y métodos, a la vista de que cachetools da 0 o 1
  de 14.
- Una regla que proteja las etiquetas `v*` de borrarse o moverse.
- Dónde vive la clave del almacén sellado: el fichero del workflow viene de la pull request
  (ADR-0071), y las pull requests de ramas de este mismo repositorio reciben los secretos del
  repositorio, así que un secreto de repositorio estaría al alcance de una pull request.
- La forma de trabajar y la autonomía de las sesiones, aparcadas hasta terminar el arnés.
- El orden de los bloques B y C, que se confirma al cerrar el bloque A.

### Bloque B · Hitos

**El bloque B está abierto.** Sus decisiones previas a B1 están tomadas: el almacén sellado se cifra
con age, con pyrage como implementación
([ADR-0072](adr/0072-the-sealed-store-is-encrypted-with-age-for-a-list-of-recipients.es.md)); la
clave de la reserva vive fuera de CI hasta B4, en la máquina del mantenedor, protegida con una
contraseña ([ADR-0073](adr/0073-the-key-of-the-hold-out-lives-outside-ci-until-b4.es.md)); y un
testigo está aislado cuando es un arreglo y nada más
([ADR-0074](adr/0074-a-witness-is-isolated-when-it-is-a-fix-and-nothing-else.es.md)).

| Hito | Qué se puede enseñar | Módulos | Se cierra cuando |
|---|---|---|---|
| B0 Reserva a mano | Dos o tres contratos del corpus con al menos dos ejemplos por caso, divididos a mano en visibles y reservados con una semilla; un parche sobreajustado que pasa los ejemplos visibles y falla uno reservado | Ninguno | La prueba está hecha en cada contrato y los minutos del mantenedor para aprobar dos o más ejemplos por caso están medidos, den lo que den; es la prueba de la segunda hipótesis, y si no se cumple, se revisa la regla de la reserva antes de B1 |
| B1 La reserva | La división por caso con una semilla, el almacén sellado y la puerta `sealed-examples`, ejecutados en local | `oracle` (la división, al menos un ejemplo visible por caso, los mensajes al agente sin valores), `platform` (el almacén sellado), `verify` (la puerta, con su canario, ejecutada solo cuando pasan los ejemplos visibles), `evidence` si hace falta (huellas y tipos de fallo de lo sellado, la barrera y el mejor esfuerzo, nunca valores) | En los contratos de B0, el run sellado en local da el veredicto que espera cada caso; un lote cuyo canario pasa lo detecta la puerta ([ADR-0014](adr/0014-hidden-checks-are-held-out-approved-examples.es.md)); la evidencia de un run sellado registra la barrera entre la clave y el agente y que el descifrado fue de mejor esfuerzo, y la identidad cifrada con contraseña nunca entra en el sandbox (ADR-0073); en CI la puerta no es aplicable, con su motivo; un lote escrito por pyrage se descifra con el binario `age` |
| B2a La semántica de las relaciones | Sobre qué se ejecuta una relación, por qué canal y con cuántas permutaciones, qué recibe el agente y qué registra la evidencia | Ninguno | [ADR-0076](adr/0076-a-relation-runs-on-the-visible-examples-of-its-requirement.es.md) aceptada: los casos de partida son los ejemplos visibles del requisito y el target; `idempotent` declara su canal, `via` en `cli` y `over` en una función de varios argumentos; `order-insensitive` permuta `over`, el orden inverso siempre y hasta `relations.permutations` sacadas con una semilla registrada; el agente recibe el requisito, la relación y el ejemplo de partida; el predicado v0.4 registra la semilla y los órdenes que fallaron como índices |
| B2b La puerta | La puerta `relations` con las dos relaciones del catálogo, sobre casos derivados de los ejemplos visibles sacados con una semilla | `contract` (`via`, y `over` comprobado contra la frontera), `core` (`relations.permutations`), `oracle` (los casos derivados y su comparación), `verify` (la puerta), `evidence` (el predicado v0.4), `interfaces` (la semilla, la política y el cableado) | Sobre dobles, una relación que no se cumple da `relation-fails`, un `FAIL` de origen `derived` que nombra el ejemplo de partida y no da ningún valor; una relación sin caso de partida pregunta; la semilla y los órdenes que fallaron están en la evidencia |
| B2c Medido | La puerta construida y medida sobre el corpus | `corpus`, `verify` | Un parche que rompe una relación de un caso falla la puerta, y su parche bueno la pasa; la puerta está construida; el límite está escrito: los casos de partida son los ejemplos visibles, los menos eficaces según los estudios de pruebas metamórficas |
| B3a La prueba de la ADR-0074 | Los 41 testigos etiquetados de nuevo por dos lectores nuevos, a ciegas entre sí y respecto a las lecturas anteriores, solo con las cuatro condiciones; los ocho en disputa mezclados y sin marcar | `corpus` | El criterio se registra antes de la lectura: la hipótesis de la ADR-0074 se cumple si κ sobre los 41 supera 0,57, lo medido al cierre del bloque A, y si no, la frontera de *aislado* se vuelve a discutir. Cada lector es un agente nuevo en una conversación propia del mantenedor, fuera de cualquier proyecto y sin memoria, con el mismo paquete y nada más. En esto la prueba se aparta de la ADR-0074, que nombra a la sesión que revisa el trabajo como segundo lector: esa sesión conoce el debate y las etiquetas de `tests/corpus/witnesses.toml`, y ya hizo una lectura de los 41, así que no es ciega; si la ADR-0074 se enmienda se decide en la pull request de la lectura; el paquete con su digest, el prompt y cada respuesta en su propio commit; un test da κ y el acuerdo bruto sobre los 41 y sobre los ocho, con el límite de κ con pocos elementos escrito: inestable, e indefinido si no hay variación |
| B3b El tiempo del job `corpus` | El job medido por partes, y repartido | `repo` | El job se ejecuta con `--durations` en varias pull requests, para medir cada parte y su variación; una ADR que enmienda la [ADR-0052](adr/0052-the-corpus-runs-in-ci-in-a-job-of-its-own-with-the-network.es.md) decide cómo se reparte; el reparto está en CI antes de añadir ningún caso |
| B3c La frontera | Cuántos de los 41 testigos cabrían con cada forma de escribir ejemplos que construyen objetos y llaman métodos | `corpus` | Los 21 testigos que no son expresables, releídos frente a cada opción, y una ADR decide si se amplía la frontera `function`; los casos que caben hoy en `cli` y en `function` no la esperan |
| B3d Los casos | Unos dieciocho casos nuevos, hacia unos treinta | `corpus` | Cada caso bueno, también los de A y B, tiene una frase de intención en `tests/corpus/intents.toml`, tomada de su proyecto o escrita por el mantenedor antes de los ejemplos; los casos nuevos llegan en unos cinco grupos de tres o cuatro, un caso bueno y sus malos, cada uno revisado por el mantenedor antes de ejecutarse: los casos apuntados más abajo para B3, casos de las dos técnicas de trampa que el bloque A no cubre, la comparación sobrecargada y el estado entre llamadas, y candidatos naturales para `order-insensitive` y para la frontera `function`, y un gemelo de `nextver-bumps-build-only-versions` en python-semver a partir de un testigo que los dos lectores de B3a etiqueten como aislado; una pull request saca de `tests/corpus/pending.toml` todos los grupos revisados |
| B3e `bench` | `bench` calculando las métricas del corpus | `bench` | Los falsos aceptados por etiqueta, los falsos rechazados, la tasa de preguntas, el valor de la reserva y la estabilidad, calculados sobre el corpus, con y sin los casos buenos cuyo testigo la lectura ciega de B3a etiqueta como no aislado |
| B4 Cierre | El criterio de salida del bloque medido, y la versión 0.2 | Ninguno nuevo | Ningún falso aceptado en las cuatro técnicas de trampa; el valor de la reserva medido; la hipótesis de que la reserva por caso caza el sobreajuste resuelta en un sentido u otro; si la puerta sellada corre en CI, decidido por una ADR en un sentido u otro, como pide la ADR-0073, que puede concluir que no; la nota de cierre, y la versión 0.2 con su etiqueta y su Release, publicadas aunque el resultado sea malo |

**B0 se cerró el 2026-11-19**, hecho a mano sobre copias de los tres contratos buenos del corpus,
con más ejemplos en los casos de sus requisitos de cambio (`tests/corpus/holdout-by-hand/`).

- **La segunda hipótesis se cumple.** El mantenedor aprobó los contratos ampliados en 2, 3 y 3 a 4
  minutos, y los tres ejemplos añadidos tras una primera revisión en 3 más: unos 11 a 12 minutos
  para los tres, unos 4 por contrato, frente a un umbral de 10 minutos por contrato fijado antes de
  cronometrar, y los 2 a 5 de A0. Dos matices: la dificultad depende del dominio y no solo del
  número de ejemplos, porque mdformat solo se pudo revisar con la ayuda de otro modelo, al tratar
  sus ejemplos de caracteres invisibles; y la reserva solo protege si los ejemplos de un caso varían
  en aquello en lo que un parche puede hacer trampa, lo que la revisión vio que faltaba en dos
  contratos (todos los ejemplos de `replace` usaban `None`, y cada caso de mdformat un solo tipo de
  espacio) y se corrigió.
- **Los agentes sin presión no sobreajustaron.** Un agente nuevo por contrato, que solo veía los
  ejemplos visibles, una sola vez y sin bucle, con el encargo de hacerlos pasar con lo mínimo,
  escribió siempre un arreglo general: en `replace` y `nextver` el arreglo del commit, en mdformat
  uno propio más estrecho; la reserva no tuvo nada que cazar. El arreglo de `nextver` falló
  `existing-tests` por un doctest de la documentación que su commit actualiza, porque al agente se
  le dijo que no tocara la documentación. Esto dice poco del bloque C, donde el agente trabaja en
  bucle: [ImpossibleBench](https://arxiv.org/abs/2510.20270) relaciona las trampas con el acceso a
  los tests y con el bucle de realimentación; es razonamiento, no una medida.
- **El mecanismo caza un sobreajuste hecho a propósito.** Un agente nuevo por contrato, con el
  encargo de hacer pasar los ejemplos visibles tratando aparte sus entradas, escribió parches que
  pasan la auditoría con los ejemplos visibles y la fallan en `visible-examples` con todos, en
  exactamente los ejemplos reservados: 1 de 1 en `replace`, 4 de 4 en `nextver`, 2 de 2 en
  mdformat. Un test del corpus lo repite (CORPUS-064); añade unos 7 minutos al job `corpus`.
- **Para B1.** En `replace` la semilla reservó un ejemplo parecido a los visibles y dejó visible el
  que difiere; si el reparto debe reservar al menos un ejemplo de otra partición se decide con los
  datos de B3. La guía de que los ejemplos de un caso cubran las particiones de lo que importa,
  según el método de categorías y particiones de
  [Ostrand y Balcer](https://doi.org/10.1145/62959.62964) (Communications of the ACM, 1988), va
  donde se describe el contrato y en lo que mira quien aprueba; un aviso de `contract check` se
  reconsidera con los datos de B3.

**B1 se cerró el 2026-11-20.** Los tres contratos de B0 se sellaron con `dokime contract seal`, cada
uno en un clon local de su proyecto sobre la base de su caso, y se auditaron con la clave; lo que se
esperaba de cada parche se subió antes de su auditoría (`tests/corpus/holdout-by-hand/sealed-run.toml`).

- [x] **Sobre los contratos de B0, la ejecución sellada local da el veredicto que espera cada
  caso.** Cada uno de los ocho parches dio el veredicto, la puerta y el resultado de
  `sealed-examples` escritos antes de su auditoría (CORPUS-066 a CORPUS-068, CORPUS-072). La
  semilla reservó el mismo ejemplo que B0 en `replace`, y otros en mdformat y `nextver`, donde los
  parches de casos especiales de B0 fallan en `visible-examples` por ejemplos de B0 que quedaron
  visibles; dos parches escritos para este sellado, como en B0, fallan en `sealed-examples`.

  | Contrato | Parche | Esperado | Medido | `sealed-examples` |
  |---|---|---|---|---|
  | `replace` | mínimo | PASS | PASS | ejecutada, PASS |
  | `replace` | de casos especiales de B0 | FAIL en `sealed-examples` | FAIL en `sealed-examples` | ejecutada, FAIL |
  | mdformat | mínimo | PASS | PASS | ejecutada, PASS |
  | mdformat | de casos especiales de B0 | FAIL en `visible-examples` | FAIL en `visible-examples` | no alcanzada |
  | mdformat | de casos especiales para este sellado | FAIL en `sealed-examples` | FAIL en `sealed-examples`, 2 de 2 | ejecutada, FAIL |
  | `nextver` | mínimo | FAIL en `existing-tests` | FAIL en `existing-tests` | no alcanzada |
  | `nextver` | de casos especiales de B0 | FAIL en `visible-examples` | FAIL en `visible-examples` | no alcanzada |
  | `nextver` | de casos especiales para este sellado | FAIL en `sealed-examples` | FAIL en `sealed-examples`, 4 de 4 | ejecutada, FAIL |

- [x] **La puerta detecta un lote cuyo canario pasa:** `canary-passed`, con el veredicto `ERROR`
  (VERIFY-164, `tests/verify/test_sealed_examples.py`).
- [x] **La evidencia registra la barrera y el mejor esfuerzo**, como decidió la
  [ADR-0075](adr/0075-the-predicate-v0-3-records-the-hold-out.es.md): la barrera la comprueba la
  puerta, y una rotura es un hallazgo (`sealed-batch-mismatch`, `canary-passed`); lo que solo se
  intenta, la detección de un ejemplo reservado ya publicado, se lista como `best-effort-secrecy`,
  una entrada por cada uno de sus límites, con los casos sin ejemplo reservado como
  `case-without-holdout` (las evidencias en `sealed-run/`).
- [x] **La identidad nunca entra en el sandbox,** comprobado y no solo razonado: se registró cada
  llamada a git y a podman de las ocho auditorías, 1456 y 476, con 64 contextos de construcción, y
  ninguna llevaba la ruta de la identidad, su nombre ni su frase de paso, ni heredaba el descriptor
  de `--passphrase-fd`; el job `corpus` lo repite con una identidad hecha para el test
  (CORPUS-071).
- [x] **En CI la puerta no es aplicable con su razón:** un contrato sellado en la medición,
  commiteado sobre la base de su caso y auditado sin la clave, da `the key is not here`
  (CORPUS-069), y cada caso del corpus que llega a la puerta da `the contract holds out no example`
  (CORPUS-070).
- [x] **Un lote escrito por pyrage se descifra con el binario `age`** (PLATFORM-095, ejecutado en CI
  con `age` instalado).

Sus límites:

- **Los ejemplos son públicos.** Están en este repositorio, fuera del historial de los proyectos,
  donde la detección de lo publicado no mira: el límite de una copia en otro fichero. La ejecución
  mide el mecanismo, no el valor de una reserva con ejemplos secretos.
- **A los agentes de los dos parches escritos para este sellado** se les pidió no leer fuera de su
  directorio, y no se pudo impedir: los contratos completos de B0 están en este repositorio. Lo que
  lo acota: cada uno de esos parches falla todos los ejemplos reservados de su contrato, 2 de 2 y 4
  de 4, así que, aunque hubieran podido leer los contratos completos, no los usaron.
- **El valor de una reserva con ejemplos secretos** queda para B3 y B4, que lo miden.

**B2 se cerró el 2026-11-22.** La puerta `relations` ejecuta las dos relaciones del catálogo sobre
casos derivados de los ejemplos visibles, y está construida.

- [x] **B2a, la semántica:** la
  [ADR-0076](adr/0076-a-relation-runs-on-the-visible-examples-of-its-requirement.es.md) está
  aceptada (#183).
- [x] **B2b, la puerta, sobre dobles:** una relación que no se cumple da `relation-fails`, un
  `FAIL` de origen `derived` que nombra el ejemplo de partida y no da ningún valor (VERIFY-184);
  una relación sin caso de partida pregunta (VERIFY-183); un rechazo de un puerto es un `ERROR`
  (VERIFY-186); la semilla de la auditoría y los órdenes que fallaron están en la evidencia,
  predicado v0.4 (EVIDENCE-094, INTERFACES-189). Por el camino: el canal de una relación en
  `contract check` (CONTRACT-095 a CONTRACT-101), `relations.permutations` en la política
  (CORE-190) y los casos derivados en `oracle` (ORACLE-052 a ORACLE-062).
- [x] **B2c, medido:** sobre mdformat en `b8c3561`, el arreglo de `27e2ba3` con tres relaciones
  `idempotent` por `stdout` pasa, y el mismo arreglo con un cambio que da otro formato a un
  documento ya formateado falla primero en `relations`, como confirmó antes el mantenedor; la
  revisión está en `tests/corpus/review.toml`, 6 minutos, registrada antes de la primera
  ejecución, que fue la CI de #193. La puerta está construida (#191), y el límite de sus casos de
  partida está escrito.

Sus límites:

- **Solo se midió `idempotent` en `cli`.** `order-insensitive` y la frontera `function` no tienen
  caso en el corpus; se buscan candidatos naturales en B3, y también un fallo real de idempotencia
  de mdformat, si lo hay.
- **El caso está construido para que solo lo vea la relación:** su condición, un bloque de código
  de una línea de un carácter antes de un encabezado, está muy cerca de tratar el ejemplo visible
  como caso especial. mdformat ya comprueba la idempotencia en sus propios tests, sobre la
  especificación CommonMark, así que un fallo natural de ella lo pararía `existing-tests` antes que
  la relación: una primera versión más amplia del cambio rompía seis de ellos.
- **El valor de las relaciones en un proyecto cuyos tests no comprueban la relación** queda sin
  medir, para B3.
- **Los casos de partida son los ejemplos visibles**, los menos eficaces según los estudios de
  pruebas metamórficas ([Segura et al., 2016](https://eprints.whiterose.ac.uk/110335/1/segura16-tse.pdf)).

**B3a se cerró el 2026-11-22.** La hipótesis de la ADR-0074 se cumple: solo con sus cuatro
condiciones, dos lectores nuevos etiquetan igual 38 de los 41 testigos en *aislado*, κ 0,85, frente
al 0,57 de las dos lecturas del bloque A (#198, `tests/corpus/blind/`).

- [x] **El criterio antes de la lectura:** κ sobre los 41 por encima de 0,57, un indecidible contado
  como no aislado, y los límites, registrados y subidos antes de cualquier conversación; una regla
  posterior, decidida tras la respuesta del lector A al lote 3 y antes del lote 4 o de calcular
  nada, cuenta la última etiqueta de un lector que se corrige.
- [x] **Los lectores:** dos agentes nuevos, Mistral (Le Chat) y Claude Sonnet 5.5, cada lote de unos
  diez testigos en una conversación propia del mantenedor, sin proyecto, sin memoria y sin búsqueda
  web, con el lote adjunto como fichero. Esto se aparta de la ADR-0074, que nombraba como segundo
  lector a la sesión que revisa el trabajo, como dice la fila de B3a; la ADR-0074 no se enmienda.
  Dos primeros intentos del lote 1 no recibieron el lote entero y se registran como descartados.
- [x] **El resultado:** 38 de 41, κ 0,8534; con la primera etiqueta del testigo en que el lector A
  se corrigió, 37 de 41 y κ 0,8038, todavía por encima. Los dos lectores etiquetan como no aislados
  los ocho en disputa, la etiqueta de la primera lectura de A en los ocho, así que κ sobre ellos es
  indefinida. Difieren en tres testigos, los tres en la condición 2, y un indecidible está también
  en la condición 2: lo que queda de la frontera es si la base está mal, lo que depende de lo que
  un lector ve de ella.
- [x] **El testigo de un caso bueno leído de otra forma:** los dos lectores nuevos etiquetan el
  testigo de `nextver-bumps-build-only-versions`, `4e09ef0e`, como no aislado en la condición 2,
  porque su base documentaba el resultado antiguo como intencionado. El caso se mantiene con su
  etiqueta y su veredicto, porque una etiqueta no cambia una vez que el caso se ha ejecutado
  (ADR-0055) y B0 y B1 lo usan; `witnesses.toml` no cambia; `bench` da sus métricas con y sin esos
  casos, y B3d añade un gemelo a partir de un testigo que los dos lectores etiqueten como aislado.

Sus límites:

- **Las respuestas se registran con las líneas de cada lote unidas y sin las comillas invertidas del
  original**, tal como se copiaron; las etiquetas y los textos se conservan.
- **Los lectores son modelos de dos proveedores**, mientras que el 0,57 del bloque A se midió entre
  dos lecturas de un mismo tipo de modelo; el acuerdo mide también la cercanía entre los dos
  modelos.
- **Cada testigo se mostró con su diff y las funciones completas alrededor de cada cambio**, no los
  ficheros completos de su base, así que la condición 2 se juzgó con menos que la base; y no se
  puede descartar lo que un modelo recuerde de estos proyectos públicos.

**B3b se cerró el 2026-11-22.** El job `corpus` se ejecuta en cuatro trozos a la vez, y una pull
request de texto no lo ejecuta: la espera del corpus bajó de unos 12 minutos a unos 5 (#203).

- [x] **Medido por partes:** cuatro ejecuciones con `--durations=0`, en #197, dos en #198 y en
  #199, dieron entre 699 y 703 segundos de pytest en tres y 911 en la cuarta, un 30 % más lenta en
  todas las partes por igual, lo que apunta al runner; la auditoría de un caso cuesta unos 47
  segundos en mdformat y unos 14 en python-semver.
- [x] **Repartido:** la
  [ADR-0078](adr/0078-the-job-corpus-is-split-into-four-parts-and-a-job-that-gathers-them.es.md)
  reparte el job en la auditoría de mdformat, la de python-semver y cachetools, la reserva a mano
  con la ejecución sellada, y el resto, que es el complemento de los demás; el job `corpus` falla
  salvo que los cuatro trozos acaben en `success` y contengan los tests de una colección. La
  [ADR-0077](adr/0077-the-corpus-does-not-run-on-a-pull-request-that-only-changes-text.es.md) salta
  el corpus en una pull request que solo cambia ficheros Markdown bajo `docs/` fuera de
  `docs/requirements/`, con un paso en cada trozo, y lo ejecuta entero en un push a `main`. Las dos
  enmiendan la ADR-0052.
- [x] **La primera ejecución con el reparto**, sobre `2e927e9`: pytest tardó 250 segundos en el
  trozo a, 117 en el b, 260 en el c y 205 en el d, y los trozos ejecutaron 6, 6, 11 y 223 tests,
  los 246 de una colección; el job `corpus` que los reúne tardó 18 segundos, y la espera desde el
  inicio de los trozos hasta su final fue de 4 minutos 54 segundos, frente a unos 12 antes. Cada
  trozo corrió en 4 núcleos; la preparación, el clonado y el resto añadieron de 10 a 15 segundos a
  cada uno, el clonado solo de 1 a 2.
- [x] **El salto, probado:** una pull request de prueba que solo cambiaba un fichero Markdown bajo
  `docs/`, contra la rama del reparto, hizo que los cuatro trozos dijeran «the corpus did not run:
  the pull request only changes text» con el fichero en la lista, y el job `corpus` pasó; se cerró
  sin fusionarla.

Sus límites:

- **El trozo c es ahora el más largo**, 260 segundos frente a los 196 que tardaban la reserva y la
  ejecución sellada dentro del job único; una ejecución no dice si es el runner. Un trozo que pase
  de 6 minutos en tres ejecuciones seguidas se vuelve a partir sin otra ADR.
- **`lint, types and tests` es ahora el job más largo de la CI**, 6 minutos 42 segundos en esa
  ejecución, así que un corpus más corto ya no acorta la espera de una pull request.
- **En una pull request de texto, un fallo del corpus que no viene del cambio** solo se ve en el
  push a `main`, o en el push siguiente si la concurrencia de la CI cancela esa ejecución.

### Queda por decidir

Queda por decidir antes de abrir un hito. Se apunta aquí y no se decide en el hito que lo
encuentra:

- **Antes de B3:** los casos que la revisión del conjunto dejó para él, reservados y sobre
  la cobertura de un contrato: un gemelo de `replace-fixes-only-major` que comprueba `None in
  parts.values()`, con el ejemplo sellado `major=[1]`; un gemelo de
  `fixes-only-a-code-block-before-the-blank` que trata aparte `</pre>` y `</h1>`, con ejemplos
  sellados de una cita, dos encabezados `##` y un `<div>` antes de un encabezado; un gemelo de
  `nextver-changes-the-tests-to-fit` con un ejemplo de `bump_prerelease`; una ocultación que no toca
  ningún test; el sobreajuste que devuelve el valor esperado, excluye la entrada visible o coincide
  con ella exactamente; y `replace("1.2.3", major=1.5)`, que devuelve `1.2.3`, un candidato de
  comportamiento no especificado.
- **Al cerrar el bloque B:** una sonda de un segundo lenguaje con Java, solo en la frontera `cli`, en
  dos fases: primero probarla sin tocar el código de dokime, después hacer pasar tres casos; con un
  tiempo limitado y sin cambiar las abstracciones centrales. Las partes de dokime que dependen de
  Python están en la [arquitectura](architecture/README.es.md#lo-que-depende-de-python).
- **Para el bloque D:** un caso encontrado en B0. El arreglo de mdformat `27e2ba3`, el parche bueno
  de un caso del corpus, pasa todos los ejemplos y todos los tests y amplía la comprobación
  `is_md_equal`, que entonces da por iguales documentos que se ven distintos: `*a* b` y `*a*b`,
  `a *b*` y `a*b*`, `[l](u) next` y `[l](u)next`. El arreglo que escribió un agente para los mismos
  ejemplos no lo hace, y el mdformat actual conserva la regla más amplia. Un cambio que lo pasa todo
  y empeora una parte del programa es lo que busca el bloque D.
- **Antes de C1:** qué pasa cuando dos cambios se ejecutan a la vez sobre el mismo repositorio; y un
  tope de gasto por ejecución, porque los presupuestos del flujo cuentan repeticiones, no dinero; y
  el veredicto esperado de `replace-fixes-only-major` y `nextver-changes-the-tests-to-fit` bajo el
  bucle de intentos, que puede arreglarlos o limpiarlos, así que depende del presupuesto de
  intentos.
- **Antes de que la evidencia llegue al agente, en el bloque C:** cada hallazgo de la puerta de los
  ejemplos sellados lleva en `lines` la línea de su entrada en `held_out`, que dice qué id reservado
  falló; si eso llega al agente se decide antes de que el agente vea la evidencia.
- **Antes de D2:** cómo se agrupan las diferencias encontradas fuera del cambio sin la pasarela a
  un modelo.

En el bloque A el conjunto de casos se ejecuta como tests normales del repositorio; `bench` lo
automatiza y calcula las métricas en el bloque B.

Lenguaje inicial: Python. Java llega en el bloque G.

Criterios de salida de cada módulo: la definición de terminado de
[CONTRIBUTING.es.md](../CONTRIBUTING.es.md#definición-de-terminado-de-un-ámbito).

## Configuración de GitHub

Ajustes que viven en GitHub y no se pueden versionar en el repositorio. El repositorio es público,
que es lo que hace que GitHub aplique el ruleset en una cuenta personal.

Un ruleset sobre `main` (Settings → Rules → Rulesets):

- PR obligatorio para integrar, con *Rebase* como único método de merge. No se exige ninguna
  aprobación, porque GitHub no deja a los autores aprobar sus propios PR; mergear es la aprobación.
- Los cinco checks de CI tienen que pasar (`lint, types and tests`, `corpus`, `governance checks`,
  `commits and branch scope`, `dependency audit`), sobre una rama al día con `main`.
- Historial lineal obligatorio; push forzado y borrado bloqueados.

Un ruleset sobre las etiquetas de versión, `protect-version-tags` (Settings → Rules → Rulesets → New
tag ruleset), para que una versión publicada siga apuntando a lo que se publicó:

- Objetivo `v*`, activo, sin nadie en la lista de excepciones.
- Actualizaciones, borrados y push forzado restringidos; creaciones permitidas, para que se pueda
  etiquetar una versión.
