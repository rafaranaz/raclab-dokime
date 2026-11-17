<!-- translation-of: ROADMAP.md sha256:25a1ece9be2d4b32 -->
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
cierra. El orden de los bloques B y C se confirma al cerrar el bloque A.

**El bloque A está abierto.** Su primer hito, A0, no tiene código: prueba a mano los formatos de los
que depende el resto del bloque.

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
| La mayoría de los requisitos reales se pueden expresar como ejemplos en una frontera | A mano, antes de cualquier código del bloque A | Se revisa el formato del contrato antes de construir |
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

Queda por decidir antes de abrir un hito. Se apunta aquí y no se decide en A2:

- **Antes de A3:** la configuración del proyecto: el adaptador de git lee los hechos del proyecto
  con `rev-parse`, que pasa por su `.git/config`. En A2 el proyecto es de quien ejecuta el arnés; en
  A3 el cambio de un agente no debe llegar a `.git/config`. El adaptador no ejecuta ningún programa
  que nombren la configuración de git en cualquier nivel, los hooks del proyecto o los atributos de
  los árboles que lee (PLATFORM-047); cuando se construya `compose_with_patch` en A3, rechaza un
  parche con una ruta que tenga una parte `.git`, que git 2.47.3 ya rechaza como ruta inválida. El
  código que se comprueba pasa a ser hostil en A3, así que el endurecimiento de A2 va antes; ya
  están construidos el lector del informe en un proceso propio, con su ruta abierta sin enlaces
  (ADR-0045), y una ejecución con `--cap-drop=ALL` y `--security-opt no-new-privileges`. El formato
  de la política, cómo se etiquetan los casos del corpus y la configuración de los tests en el pack
  los deciden la ADR-0054, la ADR-0055 y la ADR-0056. La ADR-0056 deja dos puntos para cuando se
  abra A3, antes de construir el gate `protected-paths`: los ficheros que guardan la configuración
  de los tests junto con la del proyecto, como hace mdformat en `pyproject.toml`; y cómo cuenta la
  autocomprobación un commit que cambia solo configuración y código. Y los doctests: pytest ejecuta
  los `docs/*.rst` de python-semver como doctests, pero su pack solo cuenta como tests `tests/**`,
  así que un parche que edite un doctest para que encaje no se vería como uno que edita tests.
- **Antes de A4:** cómo se versiona y se publica el arnés; y la historia en CI: el checkout de
  GitHub Actions es superficial por defecto, y el adaptador de git rechaza un clon superficial con
  `shallow-clone`, así que un workflow que autocompruebe un pack tiene que traer la historia
  completa. Y cómo encaja con la regla de A3 auditar una pull request que trae su propio
  contrato: en A3 el contrato se toma de la base, o se le pasa a `audit` desde fuera del parche, y
  nunca del parche, con `.dokime/` protegido sin excepción; un contrato que trae el parche no se
  distingue de uno que haya escrito su agente hasta que las aprobaciones se firmen (bloque E). La
  candidata: que el parche solo pueda traer el contrato cuya huella coincida con una aprobación,
  cuando existan las aprobaciones.
  Y el gate `repeatability` (ADR-0017): la tabla de los gates lo pone en el bloque A, y pregunta
  cuando dos ejecuciones de la verificación dan veredictos distintos, tantas como diga
  `verification.runs` de la política, pero ningún hito de A3 lo construye, así que A3 ejecuta la
  verificación una vez y su evidencia muestra el gate como no aplicable. La candidata: un
  incremento de `verify` en A4, antes de la versión 0.1, ya que el bloque A se cierra con A4.
  Y la separación fina de los mensajes de los hallazgos
  ([ADR-0064](adr/0064-the-evidence-of-a3-is-an-unsigned-statement-with-a-closed-predicate.es.md)):
  en A3 el mensaje entero de un hallazgo va a `untrusted`, porque los módulos mezclan las palabras
  de dokime con texto citado del contrato, del árbol, del parche o de la zona. El paso: un
  `message` con solo las palabras de dokime, y cada módulo que cita pasando ese texto a
  `untrusted`, un cambio de `Finding` en `core` y uno por cada uno de `contract`, `packs`,
  `oracle`, `sandbox`, `platform`, `verify` e `interfaces`. Se hace en A4, cuando la evidencia se
  muestre en las pull requests, o en cada módulo cuando se toque por otro motivo.
  Y la imagen del cambio: `visible-examples` observa en una imagen construida con el árbol del
  cambio, cuya huella A3 guarda en el registro, en el `gate.finished` de esa puerta, y la
  evidencia la liga a través de la cabeza del registro. La próxima versión del predicado añade un
  campo para ella, junto con lo que las dos notas anteriores llevan al predicado, el `repeated` de
  `repeatability` y el `message` de la separación fina, para que su versión cambie una sola vez.
- **Antes de B1:** la herramienta que cifra el contenido reservado del almacén sellado para una
  lista de destinatarios; y los casos que la revisión del conjunto dejó para él, reservados y sobre
  la cobertura de un contrato: un gemelo de `replace-fixes-only-major` que comprueba `None in
  parts.values()`, con el ejemplo sellado `major=[1]`; un gemelo de
  `fixes-only-a-code-block-before-the-blank` que trata aparte `</pre>` y `</h1>`, con ejemplos
  sellados de una cita, dos encabezados `##` y un `<div>` antes de un encabezado; un gemelo de
  `nextver-changes-the-tests-to-fit` con un ejemplo de `bump_prerelease`; una ocultación que no toca
  ningún test; el sobreajuste que devuelve el valor esperado, excluye la entrada visible o coincide
  con ella exactamente; y `replace("1.2.3", major=1.5)`, que devuelve `1.2.3`, un candidato de
  comportamiento no especificado.
- **Antes de C1:** qué pasa cuando dos cambios se ejecutan a la vez sobre el mismo repositorio; y un
  tope de gasto por ejecución, porque los presupuestos del flujo cuentan repeticiones, no dinero; y
  el veredicto esperado de `replace-fixes-only-major` y `nextver-changes-the-tests-to-fit` bajo el
  bucle de intentos, que puede arreglarlos o limpiarlos, así que depende del presupuesto de
  intentos.
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
