<!-- translation-of: 0041-the-environment-of-a-verified-project-is-a-dockerfile.md sha256:5dbf8f646036cad6 -->
# ADR-0041 · El entorno de un proyecto verificado es un Dockerfile, y su pack se prueba a sí mismo

**Estado:** aceptada

## Contexto

El hito A2 construye el entorno de un proyecto verificado a partir de su pack y comprueba que el
pack es de fiar. El [ADR-0028](0028-language-support-is-a-declarative-pack-with-levels.es.md) dice
qué es un pack y el [ADR-0016](0016-verification-in-a-container-on-base-plus-patch.es.md) cómo
corre la verificación. Dejan abierto cómo se escribe el entorno, quién lo escribe, cómo se eligen
los commits de la autocomprobación, qué herramienta construye y ejecuta, y qué se hace cumplir en
la primera versión.

## Decisión

- **Un Dockerfile.** El pack nombra un Dockerfile, el del proyecto o uno escrito junto al pack. Es
  la única forma de describir un entorno en la primera versión.
- **Nadie lo adivina.** El arnés no deduce un pack de un repositorio. Lo escribe una persona,
  usando lo que el proyecto tiene: su Dockerfile si funciona, o las órdenes de su pipeline.
- **La autocomprobación encuentra sus propios testigos.** El arnés toma los últimos commits del
  proyecto que cambian un test y código que no es test. Para cada uno, ejecuta los tests de ese
  commit sobre su padre y sobre el propio commit. Un commit es testigo cuando un test falla en el
  padre y pasa en el commit. El pack pasa con dos testigos entre los diez primeros candidatos, y
  los testigos se registran para que la siguiente ejecución use los mismos.
- **Red.** La verificación corre sin red; un motor que no pueda hacerlo no se usa. La preparación
  usa la red sin restricción en esta versión, y el resultado lo dice como no comprobado. La
  restricción a los registros permitidos del ADR-0016 se decide antes del bloque C.
- **La imagen base se registra, no se fija.** Un Dockerfile puede partir de una etiqueta móvil. El
  arnés registra la huella de la imagen que construyó y la de la base a la que resolvió la
  etiqueta.
- **Construir y ejecutar son dos órdenes.** Cada una se configura aparte, entre `docker`, `podman`
  y `buildah`. Un adaptador declara qué garantiza además de la ausencia de red: límites de
  memoria, procesador y procesos, y una raíz de solo lectura. Lo que el motor elegido no garantiza
  se registra como no comprobado.
- **Alcance de A2.** Nivel P1: entorno, construcción y tests con un informe en JUnit XML. El pack
  es `.dokime/pack.yaml` en el proyecto, o un fichero que se le da a la orden.

## Base

Leído en las fuentes:

- Deducir el entorno de un repositorio desconocido falla a menudo. En
  [EnvBench](https://arxiv.org/html/2503.14443) (994 repositorios) un script fijo configura el
  15,9% de los proyectos Python, y sobre el resto el mejor agente llega al 6,7% en Python y al
  29,5% en la JVM. [Repo2Run](https://arxiv.org/abs/2502.13681) da un 86% de 420 repositorios
  Python, contando como éxito que los tests se puedan ejecutar, pasen o no.
- SWE-bench no lo deduce: la instalación y los tests se declaran por repositorio y versión, y cada
  caso se valida con los tests que pasan de fallar a pasar.
- `devcontainer.json` define su entorno como una imagen, un Dockerfile al que apunta o un fichero
  Compose: envuelve un Dockerfile, no lo sustituye. Los Cloud Native Buildpacks construyen una
  imagen sin fichero de configuración detectando el lenguaje, que es el camino que esta decisión
  evita.
- De 2.000 repositorios con Dockerfile, el 56,1% construía y el 2,7% daba la misma imagen bit a
  bit ([estudio](https://arxiv.org/html/2602.17678v1)). Así que el Dockerfile que un proyecto
  tiene puede no funcionar, cosa que la autocomprobación detecta, y no se prometen imágenes
  idénticas.
- El manual de `buildah run` tiene `--network none`, `--cap-drop`, montajes de solo lectura y
  aislamiento sin privilegios, y no lista ningún límite de memoria, procesador o procesos ni una
  raíz de solo lectura.

Comprobado en los clones: ninguno de los tres repositorios del corpus tiene Dockerfile ni
devcontainer; los tres tienen un workflow, y dos usan tox.

De memoria, sin comprobar: que el formato de las imágenes es el estándar de OCI mientras que el
Dockerfile es un formato por uso, y que `podman` tiene los límites que le faltan a `buildah run`.
Razonamiento, sin prueba: que el Dockerfile que un proyecto tiene suele estar pensado para
desplegarlo y no para ejecutar sus tests; los números dos y diez de la autocomprobación. No
ejecutado: ninguno de los motores, que esta sesión no tiene. No se ha mirado Nix.

## Alternativas consideradas

- **El pack lleva una imagen base y una lista de órdenes, y el arnés escribe el Dockerfile.** Un
  formato más que aprender, para lo que un Dockerfile ya dice.
- **Admitir `devcontainer.json` ya.** Añade su herramienta de línea de órdenes como dependencia, y
  acaba en un Dockerfile de todos modos. Se puede añadir después a bajo coste.
- **Una herramienta que proponga el pack desde el pipeline del proyecto.** La hipótesis de la
  hoja de ruta se prueba primero a mano, sobre los tres repositorios del corpus.
- **Una persona lista los commits de la autocomprobación.** Más trabajo por cada pack, y la
  persona elige lo que le da la razón.
- **Construir ya el proxy que restringe los registros.** Ningún agente entra en el circuito hasta
  el bloque C.
- **Exigir la imagen base fijada por su huella.** Más estricto, y tampoco da imágenes idénticas.

## Consecuencias

- Un proyecto sin un Dockerfile que funcione cuesta uno para adoptarlo, escrito por una persona.
- El mismo pack puede dar garantías distintas en motores distintos, y la evidencia dice cuáles.
- Un proyecto con menos de dos commits que arreglen un defecto con un test no puede pasar la
  autocomprobación.
