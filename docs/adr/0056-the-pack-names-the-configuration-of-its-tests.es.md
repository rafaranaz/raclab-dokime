<!-- translation-of: 0056-the-pack-names-the-configuration-of-its-tests.md sha256:779ef5a7acef254f -->
# ADR-0056 · El pack nombra la configuración de sus tests, que queda protegida

**Estado:** aceptada

## Contexto

La [ADR-0016](0016-verification-in-a-container-on-base-plus-patch.es.md) hace rutas protegidas de
los tests, **su configuración** y el directorio del arnés: un cambio en ellas se quita del parche
salvo que el contrato lo permita. El pack nombra sus tests con el campo `tests.paths`, en la tabla
de campos de los [requisitos de `packs`](../requirements/packs.md#table-of-fields). Nada nombra su
configuración, así que el gate `protected-paths` de A3 no podría protegerla. Un cambio en un
`conftest.py` o en un fichero de configuración puede saltarse o reescribir tests sin tocar un
fichero de tests.

## Decisión

- **El pack gana un campo obligatorio, `tests.config`**: los patrones de las rutas que configuran
  cómo se ejecutan sus tests. Se protegen como los tests. El campo entra en la tabla de campos de
  los requisitos de `packs` cuando se abra A3.
- **Es obligatorio**, para que quien escribe un pack tenga que decir qué configura sus tests.
- **Un patrón puede no coincidir hoy con ningún fichero.** Protege un fichero que un parche
  crearía, como un `conftest.py` o un `pytest.ini` en un proyecto que no tiene ninguno.
- **Lo que el campo añade es lo que `tests.paths` no cubre ya.** Con `tests/**`, un
  `tests/conftest.py` ya está protegido; lo que queda es la configuración fuera del directorio de
  los tests, como un `.pytest.ini` en la raíz, o un `conftest.py` en la raíz o en `src/`.
- **Lo que contiene el campo depende de la herramienta de los tests y de su versión**, y por eso
  vive en el pack y no en la política. Para pytest, los ficheros que lee se enumeran en la base.
- **Los ficheros que guardan la configuración de los tests junto con la del proyecto**, como
  `pyproject.toml` o `setup.cfg`, siguen abiertos: proteger el fichero entero rechazaría cambios
  legítimos del proyecto. mdformat, en el conjunto de casos, guarda su configuración de pytest en
  `pyproject.toml`, así que esto hay que decidirlo al abrir A3, con los casos del conjunto delante.

## Base

Leído en la documentación de pytest: pytest toma su configuración del primero de `pytest.toml`,
`.pytest.toml`, `pytest.ini`, `.pytest.ini`, `pyproject.toml` (con una tabla
`[tool.pytest.ini_options]`), `tox.ini` (con una sección `[pytest]`) y `setup.cfg` (con una
sección `[tool:pytest]`) que encuentra desde el directorio de los tests hacia arriba
([pytest](https://docs.pytest.org/en/latest/customize.html)); y de los ficheros `conftest.py`, que
recoge en los directorios de los tests y por encima de ellos.

Medido el 2026-11-15:

- La lista depende de la versión. pytest 8.3.4, el de las imágenes del conjunto de casos, lee
  `pytest.ini` y `.pytest.ini` y no lee `pytest.toml` ni `.pytest.toml`; pytest 9.2 sí los lee.
- En el conjunto de casos, cachetools no tiene configuración de pytest; python-semver tiene
  `.pytest.ini` y `tests/conftest.py`; mdformat tiene `[tool.pytest.ini_options]` en
  `pyproject.toml` y `tests/conftest.py`.

Razonamiento, sin test: que un campo obligatorio hace que la persona piense en la configuración
una vez, al escribir el pack.

## Alternativas consideradas

- **Proteger una lista fija de nombres en el arnés.** Conoce una herramienta, y una versión de
  ella, en código, lo que el mapa de módulos prohíbe a `packs` ("Saber de lenguajes en código. Todo
  es declarativo").
- **Poner la lista en la política.** La política guarda valores del arnés; cómo ejecuta un
  proyecto sus tests es lo que describe el pack.
- **Dejar el campo opcional.** Un pack sin él protegería solo sus tests, y nadie lo notaría.

## Consecuencias

- Escribir un pack lleva una decisión más, y los tres packs del conjunto de casos ganan el campo.
- La comprobación de un pack rechaza un pack sin `tests.config`.
- Un pack escrito para una versión de pytest puede tener que cambiar cuando la imagen pase a otra.
- El caso abierto de los ficheros mixtos tiene que decidirse antes de construir el gate
  `protected-paths`.
- Cómo cuenta la autocomprobación un commit que cambia solo configuración y código, cuando elige
  sus candidatos con `tests.paths`, se decide en A3.
