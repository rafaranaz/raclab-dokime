<!-- translation-of: 0042-a-port-of-the-project-repository-composes-the-trees-that-are-built.md sha256:7cb1b6d43131f5e1 -->
# ADR-0042 · Un puerto del repositorio del proyecto compone los árboles que se construyen

**Estado:** aceptada

## Contexto

La autocomprobación de un pack
([ADR-0041](0041-the-environment-of-a-verified-project-is-a-dockerfile.es.md)) le pregunta a git
tres cosas sobre el proyecto verificado: qué commits tiene, qué rutas cambió cada uno y los
ficheros de un commit. Ningún puerto del
[mapa de módulos](../architecture/02-modules.es.md#puertos) las responde.

El puerto del entorno de verificación dice "construir una imagen desde un pack y un commit". Lo que
se construye muchas veces no es un commit. El lado padre de un candidato es el código del padre con
los tests del commit. En el hito A3 es el commit base con el parche aplicado
([ADR-0016](0016-verification-in-a-container-on-base-plus-patch.es.md)). El sujeto de la evidencia
es la huella del árbol resultante, no un commit
([ADR-0023](0023-evidence-is-an-attestation-bound-to-the-tree.es.md)), así que lo que se construye
tiene que conocerse por esa huella.

## Decisión

- **Un puerto propio.** `core` define un puerto del repositorio del proyecto. Lista commits, da el
  padre y las rutas cambiadas de un commit, compone árboles y extrae un árbol a un directorio. Hay
  dos adaptadores previstos: la orden `git`, en el primer bloque y en `platform`, y una biblioteca
  de git.
- **El puerto compone; el dominio decide qué.** El puerto ofrece dos composiciones: el árbol de un
  commit con un conjunto de rutas tomadas de otro commit, y el árbol de un commit con un parche
  aplicado. Tomar rutas de otro commit significa que bajo esas rutas el resultado tiene exactamente
  los ficheros del otro commit: un fichero que borró no está, un fichero que añadió está. Qué rutas
  son tests lo decide el módulo que tiene la regla (`packs` en la autocomprobación), no el
  adaptador.
- **Un árbol se nombra por su huella de árbol de git.** Cada composición devuelve esa huella. El
  directorio que recibe el entorno se extrae de la huella, byte a byte: sin los atributos del
  proyecto (`export-ignore`, `export-subst`, `eol`, filtros) y sin la configuración de git de la
  persona (`core.autocrlf`). El directorio no lleva `.git`.
- **Un árbol con un submódulo se rechaza.** En el árbol un submódulo es solo una referencia a un
  commit de otro repositorio, y al extraerlo queda un directorio vacío, que no es lo que nombra la
  huella. El rechazo nombra el submódulo.
- **El repositorio del proyecto solo se lee.** Los objetos que escribe una composición van a un
  directorio del arnés que usa los objetos del proyecto como alternativos. No se escribe nada en el
  `.git` del proyecto.
- **El entorno no sabe nada de git.** El puerto del entorno de verificación recibe un Dockerfile y
  un directorio; construye y ejecuta. No puede comprobar que un directorio contiene un árbol dado,
  así que no recibe la huella. Quien lo llama registra la huella del árbol que compuso junto a la
  huella de la imagen construida con él.
- **Una versión mínima de git.** El adaptador comprueba la versión de git al arrancar y rechaza una
  anterior a la 2.41, la primera con `--attr-source`.

El orden en que se listan los commits no se decide aquí.

## Base

Comprobado el 2026-11-12 con git 2.47.3, docker 29.9.3, podman 5.4.2 y buildah 1.39.3, sobre clones
locales del corpus, sin tocar los originales.

- Los tres motores construyen desde un directorio y un Dockerfile que está fuera de él
  (`build -f`). La autocomprobación de cachetools dio los mismos siete testigos de diez en los tres
  motores, con los veinte informes JUnit iguales test a test.
- Un árbol se compone sin tocar los ficheros del proyecto, con un índice desechable. El padre de
  `e963102` con sus tests dio el árbol `d5ff931…`, cuya extracción es igual al directorio que usó la
  autocomprobación. La base con el diff completo de `e963102` dio exactamente el árbol de
  `e963102`.

  ```sh
  export GIT_INDEX_FILE=$TMP/index
  git read-tree "$commit^"
  git ls-files -- tests/ | git update-index --force-remove --stdin
  git ls-tree -r "$commit" -- tests/ | git update-index --index-info
  git write-tree                                  # parent side
  git read-tree "$base" && git apply --cached patch.diff && git write-tree   # base plus patch
  ```

- En un repositorio hecho para la prueba, con un commit que borró `tests/test_old.py`, añadió
  `tests/test_new.py` y añadió un submódulo: la composición de arriba dejó fuera `test_old.py` y
  puso `test_new.py`; extraer el árbol del commit dio `vendor/sub` como un directorio vacío.
- `git archive` no da el árbol. En un commit que marca un test como `export-ignore`, un fichero como
  `export-subst` y `*.py` como `eol=crlf`, el archivo del árbol dejó fuera el test y su huella fue
  otra. El archivo del commit además sustituyó `$Format:%H$`. `checkout-index` escribió CRLF en 21
  ficheros. Leer los atributos del árbol vacío y forzar el fin de línea dio un directorio igual byte
  a byte a los blobs. `core.autocrlf=true` en la configuración global cambió 45 ficheros hasta que
  se aisló la configuración; puesto en el `.git/config` del proyecto, lo anuló `-c`.

  ```sh
  export GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_NOSYSTEM=1 GIT_INDEX_FILE=$TMP/index
  empty=4b825dc642cb6eb9a060e54bf8d69288fbee4904
  git -c core.autocrlf=false -c core.eol=lf --attr-source=$empty read-tree "$tree"
  git -c core.autocrlf=false -c core.eol=lf --attr-source=$empty checkout-index -a --prefix="$dir/"
  ```

- En un clon recién hecho, componer los árboles de `c8b4ee2` escribió dos objetos. Con las variables
  de abajo fueron al directorio del arnés, el `.git` del proyecto quedó igual byte a byte y no
  conocía el árbol nuevo. La misma composición sin ellas cambió el `.git`.

  ```sh
  export GIT_OBJECT_DIRECTORY=$TMP/objects GIT_ALTERNATE_OBJECT_DIRECTORIES=$project/.git/objects
  ```

Leído en las fuentes: las notas de la versión 2.41.0 de git dicen que `git --attr-source=<tree> cmd`
es una forma nueva de leer los atributos de un objeto árbol en lugar de la copia de trabajo; las de
la 2.43.0 corrigen un fallo de `merge-tree` con esa opción, que esta decisión no usa. Solo se
ejecutó git 2.47.3. El arnés de
[SWE-bench](https://github.com/SWE-bench/SWE-bench/blob/main/swebench/harness/run_evaluation.py)
guarda el repositorio con su `.git` en la imagen y aplica el parche dentro del contenedor con
`git apply`, y si falla con `patch`. Un comentario de ese fichero dice que su script de evaluación
borra los ficheros de test y los vuelve a aplicar; el script en sí no se leyó.

Razonamiento, sin prueba: que un puerto sirve mejor que dos (la historia aparte de los árboles);
que un proyecto cuya versión viene solo de `setuptools-scm` no se construye sin `.git` (cachetools
lo declara pero toma la versión del código, comprobado); que un fichero guardado en Git LFS se
extrae como su puntero; que en un sistema de ficheros que no distingue mayúsculas de minúsculas,
como el de macOS por defecto, dos rutas que solo difieren en eso chocan y el directorio deja de
ser el árbol. El segundo adaptador es una elección razonada; no se probó ninguna biblioteca.

## Alternativas consideradas

- **El entorno construye un commit**, como dice el mapa de módulos. El lado padre y la base con el
  parche no son commits.
- **Aplicar el parche y los tests dentro del contenedor**, como hace SWE-bench. Necesita git en la
  imagen y un árbol con escritura, y la huella de lo que se ejecutó se calcularía dentro de la zona
  que ejecuta código ajeno.
- **Extraer con `git archive`.** Los atributos del proyecto cambian lo que se extrae, así que el
  directorio no es el árbol que nombra su huella.
- **Componer en el `.git` del proyecto.** Más sencillo, y escribe objetos en el repositorio de la
  persona.
- **Dar la huella al entorno.** Solo podría etiquetar la imagen con ella; no puede comprobarla.
- **Extraer los submódulos de sus propios repositorios.** Necesita esos repositorios, quizá por la
  red, y la huella del árbol no cubriría sus ficheros.
- **Dos puertos**, uno para la historia y otro para los árboles. Los dos hablan con el mismo
  repositorio con la misma herramienta; la separación se puede hacer más tarde si un segundo
  adaptador la necesita.

## Consecuencias

- Lo que se construyó y lo que nombra la evidencia son el mismo árbol, sean cuales sean los
  atributos del proyecto o la configuración de la persona.
- La garantía dura solo mientras se prueba. Los tests del adaptador guardan un repositorio con
  `export-ignore`, `export-subst`, `eol` y `core.autocrlf`, un test borrado y un submódulo, y
  comprueban la extracción byte a byte y el rechazo.
- Un git anterior a la 2.41 se rechaza.
- Un proyecto con submódulos no se puede verificar en la primera versión.
- Un proyecto que necesita `.git` para construirse o para ejecutar sus tests no se puede verificar
  tal cual; su pack tiene que aportar lo que falta, por ejemplo una versión para `setuptools-scm`.
- Límite conocido: en un sistema de ficheros que no distingue mayúsculas de minúsculas, un árbol
  con dos rutas que solo difieren en eso no se extrae fielmente.
- El directorio de objetos de cada ejecución lo limpia el arnés.
- `platform` gana un adaptador más, y el puerto del entorno de verificación cambia su contrato.
