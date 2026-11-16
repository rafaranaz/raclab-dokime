<!-- translation-of: 0059-a-mixed-file-protects-the-section-that-configures-the-tests.md sha256:e941bc33e2281a2d -->
# ADR-0059 · Un fichero mixto protege la sección que configura los tests

**Estado:** propuesta

## Contexto

La [ADR-0056](0056-the-pack-names-the-configuration-of-its-tests.es.md) protege la configuración de
los tests con `tests.config`, y deja abiertos los ficheros que guardan la configuración de los tests
junto con la del proyecto, como `pyproject.toml` o `setup.cfg`: proteger el fichero entero
rechazaría cambios legítimos del proyecto. En el conjunto de casos, mdformat guarda su
configuración de pytest en `pyproject.toml`. La
[ADR-0058](0058-existing-tests-runs-the-tests-of-the-base-on-the-code-of-the-patch.es.md) toma
`tests.config` de la base para `existing-tests`, y también deja abiertos estos ficheros.

## Decisión

- **El pack nombra cada fichero mixto con la sección que configura sus tests**, como
  `pyproject.toml` con `[tool.pytest.ini_options]`, `setup.cfg` con `[tool:pytest]` o `tox.ini`
  con `[pytest]`. La sección la declara el pack, así que `packs` no conoce pytest. La sintaxis es un
  requisito de `packs`.
- **Un cambio en esa sección cuenta como un cambio de los tests para `protected-paths`.** El resto
  del fichero queda libre.
- **El pack pone en `tests.config` los ficheros que pytest leería antes que el fichero mixto**,
  aunque no existan, como permite la ADR-0056 con un patrón que no coincide con ningún fichero. Si
  no, un parche que añade un `pytest.ini` en la raíz dejaría sin efecto la sección protegida sin
  tocarla.
- **Autorizar un fichero mixto en `may_modify_tests` autoriza solo su sección.**
- **`existing-tests` no restaura esa sección.** Si cambió, `protected-paths` ya da `FAIL` salvo que
  el contrato lo autorice. Es un límite declarado: un fichero mixto lo vigila una sola puerta, no
  dos como quiere la ADR-0058 para los tests.

## Base

Leído en el commit del conjunto (`56b24ef`): el `pyproject.toml` de mdformat tiene
`[tool.pytest.ini_options]` con `addopts = "--strict-markers --strict-config"` y
`xfail_strict = true`. Un parche que añada ahí `--deselect` o `-p no:…` a `addopts` cambia qué
tests se ejecutan sin tocar un fichero de tests.

Medido el 2026-11-16 con pytest 8.3.4 en la imagen del conjunto, por el `configfile` que informa
pytest, con cada par de ficheros en un directorio: `pytest.ini` gana a todos, aunque esté vacío;
después `.pytest.ini`; después `pyproject.toml`, solo con `[tool.pytest.ini_options]`; después
`tox.ini`, solo con `[pytest]`; después `setup.cfg`, solo con `[tool:pytest]`. `pytest.toml` no se
lee. Cuando la orden nombra un directorio, como el pack de mdformat nombra `tests`, un `pytest.ini`
en ese directorio gana al `pyproject.toml` de la raíz. Para mdformat, entonces, un parche que añade
un `pytest.ini` vacío en la raíz sustituye `[tool.pytest.ini_options]` por ninguna configuración,
y quita `--strict-markers`, `--strict-config` y `xfail_strict`; su pack pone `pytest.ini` y
`.pytest.ini` en `tests.config`, y el de `tests/` ya está bajo `tests.paths`. La lista depende de
la versión de pytest, como dice la ADR-0056.

Leído: los ataques documentados a benchmarks de agentes van por la configuración que carga pytest
([BenchJack, sección 3](https://arxiv.org/abs/2605.12673), sobre SWE-bench) y por el propio proceso
de los tests, parcheando el informe o llamando a `sys.exit(0)`
([una entrada de tianpan.co](https://tianpan.co/blog/2026-04-17-specification-gaming-production-ai-agents), de abril de 2026, fuente secundaria). La segunda vía confirma el límite de la [ADR-0010](0010-threat-model.es.md):
los tests se ejecutan en el proceso del código que se comprueba.

Buscado y no encontrado: una herramienta que proteja la configuración de pytest por sección.

Razonamiento, sin test: que una sección cambia por los tests mucho menos que el resto de un fichero
mixto, así que protegerla rechaza pocos cambios legítimos.

## Alternativas consideradas

- **Proteger el fichero entero.** Rechaza cambios legítimos del proyecto, como sus dependencias o
  su versión.
- **No protegerlo.** Un parche podría añadir `--deselect` o `-p no:…` a `addopts` y ninguna puerta
  lo vería.
- **Proteger la sección y además ejecutar `existing-tests` con la sección de la base**, mediante un
  `pytest.ini` generado a partir de ella y `-c`. Más fuerte, pero hay que demostrar que pytest se
  comporta igual con el fichero generado, y hace falta escribir la sección en un árbol.

## Consecuencias

- `protected-paths` lee la sección de un fichero mixto en la base y en el parche y las compara, así
  que lee TOML e INI sin saber qué significa la sección.
- `existing-tests` se ejecuta con la sección del parche, la haya autorizado el contrato o no; si no
  la autorizó, `protected-paths` ya ha dado `FAIL`.
- Un fichero mixto tiene una puerta donde un fichero de tests tiene dos.
- Los packs del conjunto que tienen un fichero mixto ganan su sección cuando se construya el campo
  en A3.
