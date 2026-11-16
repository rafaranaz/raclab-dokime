<!-- translation-of: 0060-only-the-tests-make-a-commit-a-candidate-of-the-self-check.md sha256:ccfc442027fe59a2 -->
# ADR-0060 · Solo los tests hacen candidato a un commit de la autocomprobación

**Estado:** aceptada

## Contexto

La autocomprobación de un pack toma como candidatos los commits que cambian un test y código que
no es un test, y ejecuta los tests del commit sobre su padre y sobre el commit
([ADR-0041](0041-the-environment-of-a-verified-project-is-a-dockerfile.es.md)). Hoy una ruta es un
test cuando coincide con `tests.paths`, y lo demás es código (PACKS-020, PACKS-021), así que la
configuración de los tests cuenta como código. La
[ADR-0056](0056-the-pack-names-the-configuration-of-its-tests.es.md) añade `tests.config` y deja
abierto cómo cuenta la autocomprobación un commit que cambia solo configuración y código; la
[ADR-0059](0059-a-mixed-file-protects-the-section-that-configures-the-tests.es.md) añade la sección
de pytest de un fichero mixto.

## Decisión

Esto enmienda la ADR-0041 en la regla de un candidato y en cómo se compone el lado del padre.

- **Solo las rutas de `tests.paths` hacen candidato a un commit.** Un candidato cambia un test y
  código; los ficheros de `tests.config` no son ni lo uno ni lo otro, así que un commit que cambia
  solo configuración y código no es candidato.
- **Un commit que cambia la sección de pytest de un fichero mixto no es candidato.** El lado del
  padre tendría que tomar esa sección del commit, lo que obliga a reescribir parte de un fichero
  TOML o INI en un árbol; dejar fuera el commit lo evita.
- **El lado del padre toma del commit sus tests y los ficheros de `tests.config`**, para que lo
  único que distinga los dos lados sea el código. Son rutas enteras, que `compose_with_paths` ya
  compone. Esto cambia PACKS-061, que solo toma los tests.

## Base

Razonamiento, sin test: un cambio de configuración en el commit puede crear un testigo falso de dos
formas. Puede hacer pasar a verde un test sin arreglar nada, dejando de convertir un aviso en un
error. Y puede hacer aparecer un test, dejando de excluirlo (quitando un `--deselect`, o ampliando
`testpaths`): ese test falta en el informe del padre, y PACKS-033 cuenta el commit como testigo
cuando el padre tiene cualquier otro fallo. Esconder un test en el commit, excluyéndolo o marcándolo
como `xfail`, no crea un testigo, porque un testigo necesita un test que pase en el commit. Con la
configuración del commit en los dos lados, el test también se ejecuta en el padre, sobre su código,
y un test que pasa de rojo a verde lo hace por el código.

## Alternativas consideradas

- **Mantener la configuración como código**, como hoy. Un commit que cambia un test y su
  configuración y nada más sería candidato, y la configuración podría hacerlo un testigo falso.
- **Contar la configuración como un test.** Un commit que cambia solo configuración y código sería
  candidato, sin nada en sus tests que pase de rojo a verde salvo lo que selecciona la
  configuración.
- **Componer la sección de pytest de un fichero mixto en el lado del padre.** Mantiene esos commits
  como candidatos, a costa de reescribir TOML e INI dentro de un árbol.

## Consecuencias

- PACKS-030, PACKS-031 y PACKS-061 cambian cuando se construyan el campo `tests.config` y las
  secciones de la ADR-0059 en A3.
- Los packs del conjunto pueden tener otros candidatos cuando declaren su configuración, así que el
  job `corpus` los mide otra vez entonces.
- Los commits que cambian la sección de pytest de un fichero mixto se pierden como candidatos;
  cuántos no está medido.
