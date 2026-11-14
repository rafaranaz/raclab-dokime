<!-- translation-of: 0045-a-test-report-is-read-by-a-bounded-reader-that-refuses-any-dtd.md sha256:9db17c213ebb36cd -->
# ADR-0045 · Un informe de tests lo lee un lector acotado que rechaza cualquier DTD

**Estado:** aceptada

## Contexto

La [ADR-0041](0041-the-environment-of-a-verified-project-is-a-dockerfile.es.md) hace que el pack
nombre un informe en JUnit XML que la orden de tests escribe en el directorio de salida. El código
que lo escribe es el código que se prueba, y en el hito A3 el cambio de un agente: puede escribir
un informe de cualquier tamaño, poner un enlace donde debería estar el informe o declarar entidades
que se expanden sin fin. La autocomprobación de un pack lee esos informes ya, y `verify` los lee
en A3.

## Decisión

### Quién lo lee

- **El adaptador del entorno de verificación lee el informe.** Lo lee después de la ejecución y da
  el resultado de cada test al módulo que llamó al puerto. El dominio recibe valores y no hace
  entrada ni salida.
- **El resultado de un test es un tipo de `core`.** `Outcome` y `Report`, hoy en
  `src/dokime/packs/selfcheck.py`, pasan a `core`, porque el puerto los devuelve y un adaptador
  solo importa `core`.
- **Los límites son política, y el adaptador los recibe.** `core` define los límites de lectura de
  un informe como un valor, junto a `Outcome` y `Report`, con los tres límites de abajo. El módulo
  que llama al puerto (`packs`, y `verify` en A3) pasa ese valor en cada llamada. En la primera
  versión no lo cambian ni el pack ni una opción de la orden.

### Límites y códigos

Cada fallo es un hallazgo con el veredicto `ERROR`. El módulo que llamó al puerto lo añade a su
resultado.

| Caso | Código |
|---|---|
| El informe ocupa más de 32 MiB. Se lee como mucho el límite más un byte. El pack no puede subir el límite. | `report-too-large` |
| La ruta tiene un enlace simbólico en cualquiera de sus partes, o el informe no es un fichero regular. La ruta se abre parte a parte desde el directorio de salida, cada parte con `O_NOFOLLOW`. | `report-not-a-file` |
| El informe tiene un `DOCTYPE`. Se rechaza con manejadores de `pyexpat`, antes de que se declare ninguna entidad. | `report-has-doctype` |
| El informe no es XML bien formado. | `report-unreadable` |
| El proceso que lee el informe muere o llega a un límite. | `report-reader-failed` |
| El Expat del Python que ejecuta el arnés es anterior a la 2.8.5. Se comprueba al arrancar el adaptador. | `expat-too-old` |

### Un proceso propio

- **El informe se lee en un proceso propio.** Ese proceso tiene `RLIMIT_AS` en 512 MiB y
  `RLIMIT_CPU` en 10 segundos. El adaptador abre el fichero y le pasa el descriptor ya abierto, así
  que el proceso nunca resuelve la ruta.
- **Esto acota la memoria y el tiempo de procesador, y convierte una caída del analizador en
  `ERROR`. No es un aislamiento.** El proceso corre con los permisos de la persona. Si un defecto
  de Expat permitiera ejecutar código, ese código podría hacer lo que puede hacer la persona.
- **Se registra la versión de Expat.** El valor de `pyexpat.EXPAT_VERSION` va en la evidencia.
- **El mínimo de Expat vive en el adaptador, no en `core`.** Es una constante del adaptador que lee
  los informes, junto a la comprobación que se hace al arrancar el adaptador. No es política: dice
  qué versiones del analizador que usa este adaptador se sabe que no son seguras, así que quien
  llama no tiene motivo para pedir otra, y un adaptador con otro analizador tendría otro mínimo.
  Subirlo es un cambio solo de `sandbox`, cuyo commit cita la entrada del fichero `Changes` de
  Expat que lo justifica. Como la evidencia registra la versión encontrada, una ejecución se puede
  juzgar después contra un mínimo más reciente.

## Base

Comprobado el 2026-11-12 y el 2026-11-13 con Python 3.13 y Expat 2.9.0, sobre los informes de las
autocomprobaciones del corpus (cachetools, python-semver, mdformat).

- **Informes.**
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
- **Ruta.** Abrir la ruta parte a parte con `O_NOFOLLOW` y `dir_fd`, y comprobar con `fstat` que
  es un fichero regular, rechazó:
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
- **Imports.** El contrato "Adapters import only core" de `lint-imports` impide que `sandbox`
  importe `packs`, donde hoy vive `Outcome`.

No comprobado: macOS y Windows; si macOS hace cumplir `RLIMIT_AS`; informes de herramientas que no
sean pytest. Razonamiento, sin prueba: que un pack no necesita un informe mayor en la primera
versión (32 MiB caben unos 300 000 tests al tamaño medido); los límites de 512 MiB y 10 s del
lector; que el lugar correcto para dar los límites es quien llama, y no el adaptador ni la raíz de
composición, y que el lugar correcto para el mínimo de Expat es el adaptador.

## Alternativas consideradas

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
- **El adaptador devuelve los bytes y `packs` los analiza.** El dominio arrancaría un proceso para
  acotar el analizador, y eso es entrada y salida.
- **Los límites como constantes del adaptador.** El mapa de módulos dice que `sandbox` no decide la
  política, la recibe.
- **Los límites los da `interfaces` al construir el adaptador.** La raíz de composición tendría un
  valor de política, y `verify` no podría pedir límites distintos de los de la autocomprobación.
- **El mínimo de Expat en `core`, con los límites.** `core` nombraría una biblioteca que solo usa un
  adaptador, y quien llama podría bajar un suelo de seguridad.
- **El mínimo de Expat como restricción del proyecto**, en `pyproject.toml`. Expat viene con la
  compilación de Python, a menudo enlazado con la biblioteca del sistema, no con un paquete, así
  que ninguna restricción de dependencias puede exigirlo.
- **Un campo del pack para subir el límite del informe.** El código que se comprueba elegiría su
  propio límite, y ningún pack del corpus se acerca a él.

## Consecuencias

- `verify` en A3 lee los informes con el mismo adaptador, y por tanto con los mismos límites salvo
  que pase otros.
- Un informe que el arnés no puede leer nunca aprueba. Termina en `ERROR`, y lo mira una persona.
- En Windows no hay `dir_fd`, así que la apertura segura del informe no funciona allí: límite
  conocido.
- Un arnés sobre un Python cuyo Expat sea anterior a la 2.8.5 rechaza leer informes. El mínimo se
  revisa aparte, en `sandbox`, cuando Expat publique arreglos.
- El proceso que lee el informe acota los recursos. No contiene un defecto de Expat que permita
  ejecutar código.
- `Outcome` y `Report` se mueven en dos ramas, una por alcance: `core` los añade, y después `packs`
  los importa de `core` y quita los suyos.
- Cambia la fila del entorno de verificación en el mapa de módulos: también lee el informe y da el
  resultado de cada test.
