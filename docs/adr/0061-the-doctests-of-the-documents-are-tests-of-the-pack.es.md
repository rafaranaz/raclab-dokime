<!-- translation-of: 0061-the-doctests-of-the-documents-are-tests-of-the-pack.md sha256:8d786f66b52685b2 -->
# ADR-0061 · Los doctests de los documentos son tests del pack, y los de los docstrings son un límite declarado

**Estado:** propuesta

## Contexto

pytest puede ejecutar como tests los ejemplos de un documento o de un docstring. python-semver lo
hace, y su pack solo cuenta como tests `tests/**`. Un parche que edite un doctest de un documento
para que encaje no se vería como uno que edita tests, y la
[ADR-0058](0058-existing-tests-runs-the-tests-of-the-base-on-the-code-of-the-patch.es.md) no lo
tomaría de la base. La
[ADR-0057](0057-the-cases-of-the-corpus-come-from-witnesses-that-fit-a-boundary.es.md) toma como
parche bueno todo lo que el commit cambia fuera de los tests del pack, documentación incluida.

## Decisión

Esto enmienda la ADR-0057 en qué es el parche bueno; el resto se mantiene.

- **Los documentos cuyos ejemplos ejecuta pytest son tests**, y van en `tests.paths` de su pack.
  Para python-semver eso es `docs/**/*.rst`, que también toma los ficheros de la raíz de `docs/`:
  pytest también los recoge.
- **Un arreglo que cambia el comportamiento que documenta un doctest tiene que actualizarlo**, y el
  contrato autoriza ese fichero en `may_modify_tests`. Con la ADR-0058 se ejecuta el doctest de la
  base, que espera el comportamiento antiguo, así que sin esa autorización un parche bueno daría
  `FAIL`.
- **El parche bueno es todo lo que el commit cambia fuera de las rutas de los tests del pack, más
  los ficheros que su contrato autoriza en `may_modify_tests`.** El caso
  `python-semver/nextver-bumps-build-only-versions` autoriza
  `docs/usage/increase-parts-of-a-version_prereleases.rst`.
- **Los doctests de los docstrings son un límite declarado.** Cuando un proyecto tiene su código en
  `testpaths`, o un pack nombra `src/` en su orden, `--doctest-modules` hace tests de los
  docstrings del código: tests dentro de ficheros de código, que no se pueden proteger por ruta sin
  proteger el código, ni restaurar sin deshacer el arreglo. Un parche que edite el ejemplo de un
  docstring para que encaje no lo ve ninguna puerta del bloque A. Cómo lo señalan el pack y la
  evidencia se decide al construir la puerta.

## Base

Leído en python-semver, en `b6e83e3`, `a8bb4f89` y `15a42d0`: `.pytest.ini` tiene
`testpaths = tests docs`, `--doctest-glob='*.rst'` y `--doctest-modules`. La orden de su pack no
nombra ninguna ruta, así que pytest usa `testpaths`, y los doctests de `docs/` ya se ejecutan en su
autocomprobación.

Medido el 2026-11-16 en la imagen del conjunto, en `b6e83e3`: pytest recoge 534 tests, y los 21
que están fuera de `tests/` son todos `docs/**/*.rst`. Ninguno viene de `src/`, porque
`--doctest-modules` solo recorre lo que está bajo `testpaths`. Así que python-semver no tiene el
límite de los docstrings; se declara para los proyectos que lo tendrían.

Medido el mismo día, la autocomprobación de python-semver con `docs/**/*.rst` en `tests.paths`
pasa en 22 s. Su primer testigo es `b6e83e3`, "Bump version 3.1.0 -> 3.1.1": su test es
`docs/usage/semver-version.rst`, cuyo `>>> semver.__version__` pasa de `'3.1.0'` a `'3.1.1'`. Para
la autocomprobación no es falso: muestra que la orden ejecuta tests y que se ve un rojo que pasa a
verde, que es lo que la autocomprobación tiene que probar. Como arreglo sí lo es, y para los casos
del conjunto eso es lo que quita el filtro *aislado* de la ADR-0057.

Medido el 2026-11-16 por la sesión que construyó los casos, con pytest 8.3.4 en local y no en el
contenedor, sobre los 25 primeros candidatos de python-semver con `docs/**/*.rst` en `tests.paths`:
21 testigos, frente a 18 entre sus 25 primeros candidatos con solo `tests/**`. De los 21:

- 5 son subidas de versión o cambios de configuración cuyo único test que pasa a verde es
  `docs/usage/semver-version.rst`: `b6e83e3`, `9c19156`, `bae0b7c`, `cc4ae07` y `6208a54`;
- 1 es un arreglo que antes no se veía, porque su único test es un doctest: `fdec4ae`,
  "fix(next_version): reset prerelease when token changes";
- los commits de los casos, `0bd62d4` y `4e09ef0`, siguen siendo testigos con los mismos tests, así
  que los casos no cambian.

## Alternativas consideradas

- **Dejar los documentos fuera de `tests.paths`.** Un parche que edite un doctest para que encaje
  no se vería como uno que edita tests, y `existing-tests` ejecutaría el doctest editado.
- **Mantener el parche bueno como todo lo que está fuera de los tests.** El parche bueno de
  `nextver` no llevaría el doctest que actualiza, y con el doctest de la base daría `FAIL`.
- **Proteger los ficheros de código que tienen doctests.** Cada arreglo tocaría una ruta protegida.

## Consecuencias

- Los candidatos de python-semver cambian con `docs/**/*.rst` en `tests.paths`; la búsqueda de
  testigos de la ADR-0057 se repitió para ese proyecto, y su resultado está en la base.
- Una versión publicada que actualiza la versión que muestra un doctest es un testigo de la
  autocomprobación; nunca llega a ser un parche bueno, porque no está aislada.
- El pack de python-semver cambia en una pull request del ámbito `corpus`, después de esta.
- El límite de los docstrings queda escrito antes de que ningún proyecto del conjunto lo tenga.
