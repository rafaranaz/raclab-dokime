<!-- translation-of: 0044-how-the-self-check-of-a-pack-runs-and-reads-its-reports.md sha256:2487e7f8f6fdeed3 -->
# ADR-0044 · Cómo se ejecuta la autocomprobación de un pack y cómo lee sus informes

**Estado:** propuesta

## Contexto

La [ADR-0041](0041-the-environment-of-a-verified-project-is-a-dockerfile.es.md) dice qué prueba la
autocomprobación de un pack: entre los últimos commits que cambian un test y código que no es test,
al menos dos de los diez primeros tienen un test que falla en el padre y pasa en el commit. La
[ADR-0042](0042-a-port-of-the-project-repository-composes-the-trees-that-are-built.es.md) da el
puerto que compone los árboles, y la
[ADR-0043](0043-tests-run-only-on-an-engine-that-enforces-the-limits.es.md) los motores que los
ejecutan. Quedaba abierto qué módulo dirige el bucle, qué significa "los últimos commits" y cómo se
lee un informe en JUnit XML cuando el código que lo escribió no es de fiar. En el hito A3 ese código
es el cambio de un agente.

## Decisión

### Quién la ejecuta

- **`packs` dirige la autocomprobación.** Elige los candidatos, pide al puerto del repositorio del
  proyecto cada árbol, ejecuta los tests en los dos lados y aplica la regla de los testigos. Recibe
  los puertos de `interfaces`.
- **Una operación reutilizable.** El bucle se apoya en una operación de `packs`: ejecutar los tests
  de un pack sobre un directorio y dar el resultado de cada test. `verify` usa la misma operación
  en el hito A3.

### El orden de los candidatos

- **El puerto da la historia y `packs` la ordena.** El puerto del repositorio del proyecto da la
  historia desde un commit: todos los commits alcanzables desde él, con su fecha de commit y sus
  padres en el orden en que el commit los nombra. Esto enmienda la ADR-0042, donde el puerto lista
  commits.
- **La regla de orden es nuestra.**
  - Ningún commit va antes que un commit que desciende de él.
  - Entre los commits que pueden ir a continuación, va primero el de fecha de commit más reciente.
  - Si las fechas son iguales, va primero el que pudo ir a continuación antes. Los padres de un
    commit pasan a poder ir a continuación en el orden en que el commit los nombra.
  - Un commit que no tiene exactamente un padre se deja fuera, a propósito. Eso quita los merges
    y los primeros commits, y un candidato necesita un padre.
- **Lo que tiene que hacer un adaptador del repositorio.** Ignora los objetos de reemplazo
  (`git replace`) y rechaza un clon superficial.

### Qué cuenta

- **Un testigo es un test que pasa de rojo a verde.** No es un commit que corrige un defecto.
  Cuentan las refactorizaciones y las funciones que se quitan, porque la regla mide lo que necesita
  el pack: que el entorno muestre a un test cambiar de estado.
- **Los candidatos que no pueden ser testigos siguen siendo candidatos.** Eso incluye un commit que
  solo cambia tests y documentación, y uno cuyos tests solo se adaptaron (mdformat `10307b9`). El
  pack no tiene ningún campo para excluirlos.
- **Los números se mantienen: dos testigos entre los diez primeros candidatos.**

### Cómo se lee un informe

- **El adaptador del entorno de verificación lee el informe.** Lo lee después de la ejecución y da
  a `packs` el resultado de cada test. El dominio recibe valores y no hace entrada ni salida.
- **Límites y códigos.** Cada fallo es un hallazgo con el veredicto `ERROR`:

  | Caso | Código |
  |---|---|
  | El informe ocupa más de 32 MiB. Se lee como mucho el límite más un byte. El pack no puede subir el límite. | `report-too-large` |
  | La ruta tiene un enlace simbólico en cualquiera de sus partes, o el informe no es un fichero regular. La ruta se abre parte a parte desde el directorio de salida, cada parte con `O_NOFOLLOW`. | `report-not-a-file` |
  | El informe tiene un `DOCTYPE`. Se rechaza con manejadores de `pyexpat`, antes de que se declare ninguna entidad. | `report-has-doctype` |
  | El informe no es XML bien formado. | `report-unreadable` |
  | El proceso que lee el informe muere o llega a un límite. | `report-reader-failed` |
  | El Expat del Python que ejecuta el arnés es anterior a la 2.8.5. Se comprueba al arrancar el adaptador. | `expat-too-old` |

- **El informe se lee en un proceso propio.** Ese proceso tiene `RLIMIT_AS` en 512 MiB y
  `RLIMIT_CPU` en 10 segundos. El adaptador abre el fichero y le pasa el descriptor ya abierto, así
  que el proceso nunca resuelve la ruta. Esto acota la memoria y el tiempo de procesador, y
  convierte una caída del analizador en `ERROR`. **No es un aislamiento.** El proceso corre con los
  permisos de la persona. Si un defecto de Expat permitiera ejecutar código, ese código podría hacer
  lo que puede hacer la persona.
- **Se registra la versión de Expat.** El valor de `pyexpat.EXPAT_VERSION` va en la evidencia.
- **Un informe que no se puede leer deja la autocomprobación en `ERROR`.** El candidato no se
  descarta en silencio, para que un pack nunca se juzgue con menos candidatos de los que dice la
  regla.

## Base

Comprobado el 2026-11-12 y el 2026-11-13, sobre clones locales del corpus (cachetools `1ce79ef`,
python-semver `b6e83e3`, mdformat `56b24ef`), sin tocar los originales.

- **Autocomprobación.**
  - cachetools dio 7 testigos entre los 10 primeros candidatos, python-semver 8 y mdformat 4.
  - Un pack de cachetools que instala la versión publicada en PyPI en lugar del código que se
    prueba dio 0 de 10.
  - Entre los testigos hay refactorizaciones y funciones que se quitan.
  - Dos candidatos no pueden ser testigos por las razones de arriba: cachetools `6a89b7c` y
    python-semver `f3c7138` solo cambian tests y documentación, y mdformat `10307b9` solo adapta
    sus tests a un fixture nuevo.
- **Orden.**
  - Leído en el manual de `git rev-list`:
    - el orden por defecto es "orden cronológico inverso";
    - `--date-order` no muestra un padre antes que todos sus hijos, y por lo demás sigue la fecha
      del commit;
    - `--topo-order` da dos salidas válidas para el ejemplo del propio manual;
    - no dice nada de las fechas iguales.
  - Probado en repositorios hechos para la prueba:
    - con un hijo más antiguo que su padre, el orden por defecto mostró primero el padre, y
      `--date-order` no;
    - las fechas iguales se resolvieron por el orden de los padres en el merge;
    - la salida fue idéntica con git 2.32.0, 2.40.1, 2.47.3 y 2.54.0, con y sin grafo de commits,
      y en un clon recién hecho;
    - un `git replace --graft` cambió una lista de 7 commits a 1, y `--no-replace-objects` la
      restauró;
    - un clon con `--depth 3` dio 3 commits en lugar de 6.
  - La regla de arriba, escrita en 25 líneas de Python sobre `git log --format='%H %ct %P'`, dio
    exactamente la salida de `git rev-list --date-order --no-merges`, empates incluidos, tras
    quitar las raíces. Se comparó en seis repositorios: dos hechos para la prueba, los tres del
    corpus y el repositorio del propio git (82 925 commits, 61 446 en la lista).
  - En git, leer la historia tardó 3,4 s y ordenarla 0,65 s, con 75 MB de memoria.
- **Informe.**
  - El mayor de los 125 informes de las autocomprobaciones ocupa 462 KB: mdformat, con 4286
    tests. Ninguno tiene `DOCTYPE`.
  - Un lector hecho con `pyexpat`, con `StartDoctypeDeclHandler` y `EntityDeclHandler` que lanzan
    un error, rechazó el billion laughs, el quadratic blowup, dos entidades externas, una DTD
    externa y una petición a un servidor local. Cada uno se rechazó en menos de 0,01 s con unos
    11 MB.
  - El informe de mdformat se leyó en 0,02 s con 14 MB.
  - Un único atributo de 30 MB, por debajo del límite, ocupó 141 MB.
  - El analizador en C de ElementTree no expone esos manejadores, así que se usa `pyexpat`
    directamente.
  - Abrir la ruta parte a parte con `O_NOFOLLOW` y `dir_fd`, y comprobar con `fstat` que es un
    fichero regular, rechazó:
    - un enlace en un directorio intermedio que apunta fuera del directorio de salida;
    - un enlace en un directorio intermedio que apunta dentro;
    - un enlace como fichero final;
    - un FIFO.

    Leyó el informe normal.
- **Proceso propio**, con `RLIMIT_AS` y `RLIMIT_CPU` fijados antes de que arranque el lector:

  | Caso | Resultado |
  |---|---|
  | El informe de mdformat | 4286 tests, 0,22 s |
  | Un atributo de 30 MB con 512 MiB | leído |
  | El mismo con 64 MiB | "out of memory", salida 1 |
  | Un fallo de segmentación forzado | el proceso terminó con `SIGSEGV` |
  | Un bucle con un límite de 1 s | el proceso terminó con `SIGKILL` tras 1,24 s |

  Arrancar cada proceso hijo cuesta unos 0,075 s, unos 3 s para los 40 informes de una
  autocomprobación.
- **Expat, leído en su fichero `Changes`.** Varios defectos corregidos no necesitan DTD:

  | Versión | CVE | Qué corrigió |
  |---|---|---|
  | 2.4.5 | CVE-2022-25235 | UTF-8 mal formado en los nombres, con exploits conocidos |
  | 2.8.1 | CVE-2026-45186 | tiempo cuadrático en los nombres de atributo |
  | 2.8.4 | CVE-2026-66046, CVE-2026-76641 | tiempo cuadrático en las búsquedas de atributos (sin comprobar si necesitan DTD) |
  | 2.8.5 | CVE-2026-93990 | UTF-16 mal formado, que a un documento le basta con declarar |
  | 2.10.0, del 2026-11-02 | CVE-2026-118370 | un desbordamiento en `storeAtts` |

  El Python de aquí tiene Expat 2.9.0, así que le falta el último arreglo. El fichero empieza
  diciendo que Expat tiene fallos de seguridad sin corregir, listados en su issue 1160 sin
  detalles. Exigir la 2.10.0 rechazaría todos los Python disponibles aquí.
- **defusedxml**, leído en PyPI y en su código:
  - tiene `forbid_dtd`, desactivado por defecto, que pone los mismos tres manejadores de
    `pyexpat`;
  - carga el módulo de ElementTree en Python puro con una variante de `import_fresh_module`;
  - no acota el tamaño ni comprueba la versión de Expat;
  - su última versión estable es la 0.7.1, de 2021; la 0.8.0rc2, de 2023, nunca salió como final;
    su último commit es de octubre de 2023.

No comprobado: macOS y Windows; si macOS hace cumplir `RLIMIT_AS`; informes de herramientas que no
sean pytest. Razonamiento, sin prueba: que un pack no necesita un informe mayor en la primera
versión (32 MiB caben unos 300 000 tests al tamaño medido); los límites de 512 MiB y 10 s del
lector.

## Alternativas consideradas

- **Un servicio de dominio nuevo dirige la autocomprobación.** Duplicaría en otro módulo la regla
  que tiene `packs`. `verify`, el otro candidato, no existe en A2.
- **El orden que da `git rev-list`, exigido solo al adaptador de git.** Un segundo adaptador no
  tendría nada que cumplir. Los empates dependen de un comportamiento de git que su manual no dice.
- **`--topo-order` o el orden por fecha de autor.** El manual del primero admite dos salidas. La
  fecha de autor la pone quien escribe el commit y no es la fecha de la historia.
- **El orden en `core`.** Solo lo necesita la autocomprobación; la auditoría de A3 no.
- **Un campo del pack para excluir candidatos**, como rutas que no cuentan como código. Los tres
  packs pasan sin él.
- **defusedxml con `forbid_dtd=True`.** Funciona igual, y añade una dependencia sin versión estable
  desde 2021 que se apoya en recargar un módulo de la biblioteca estándar. No da ni el límite de
  tamaño ni la comprobación de versión.
- **Sin comprobación de versión, ya que se rechaza el `DOCTYPE`.** Varios defectos corregidos de
  Expat no necesitan DTD.
- **Leer el informe en el proceso del arnés.** Una caída del analizador terminaría el arnés, y la
  memoria solo quedaría acotada por el tamaño del fichero.
- **Leer el informe dentro del contenedor que ejecutó los tests.** Aislaría de verdad al lector. La
  imagen es la del proyecto, y el arnés tendría que fiarse de un lector que corre dentro de ella,
  escrito por el mismo código que comprueba.
- **Un campo del pack para subir el límite del informe.** Ningún pack del corpus se acerca al
  límite.

## Consecuencias

- La autocomprobación da los mismos diez primeros candidatos en cualquier máquina y con cualquier
  adaptador.
- Ordenar carga toda la historia. Se ha medido hasta 82 925 commits, no más.
- Un clon superficial no se puede autocomprobar. Tampoco un repositorio cuya historia solo difiere
  por objetos de reemplazo.
- `verify` en A3 lee los informes con la misma operación, y por tanto con los mismos límites.
- Un informe que el arnés no puede leer nunca aprueba. Termina en `ERROR`, y lo mira una persona.
- En Windows no hay `dir_fd`, así que la apertura segura del informe no funciona allí: límite
  conocido.
- Un arnés sobre un Python cuyo Expat sea anterior a la 2.8.5 rechaza leer informes. El mínimo hay
  que revisarlo cuando Expat publique arreglos.
- El proceso que lee el informe acota los recursos. No contiene un defecto de Expat que permita
  ejecutar código.
- Se enmienda la ADR-0042: el puerto da la historia en lugar de listar commits.
- El mapa de módulos cambia con esta decisión. El puerto del entorno de verificación lee el informe
  y da el resultado de cada test. El puerto del repositorio del proyecto da la historia.
