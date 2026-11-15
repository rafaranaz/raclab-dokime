<!-- translation-of: 0052-the-corpus-runs-in-ci-in-a-job-of-its-own-with-the-network.md sha256:cb01e715afe4f797 -->
# ADR-0052 · El conjunto de casos se ejecuta en CI en un job propio, con red

**Estado:** aceptada

## Contexto

El criterio de salida de A2 es que los packs de los tres repositorios del conjunto de casos se
construyan y pasen su autocomprobación. El 2026-11-15 `dokime env check` pasó sobre cachetools,
python-semver y mdformat, con packs que vivían fuera del repositorio. La hoja de ruta dice que en el
bloque A el conjunto de casos se ejecuta como tests normales del repositorio.

Un pack es nuestro; el código de cada proyecto no, y no se copia: se nombra por su repositorio y su
commit. Autocomprobar un pack necesita por tanto la red tres veces: para clonar el proyecto, para
traer la imagen base y para instalar lo que instala el Dockerfile, que la
[ADR-0041](0041-the-environment-of-a-verified-project-is-a-dockerfile.es.md) permite al preparar.
El job de tests ya trae dos imágenes pequeñas para los tests de las garantías; no trae código de
otro proyecto ni instala ningún paquete. Las tres ejecuciones tardaron 21 s, 37 s y 254 s, con las
imágenes ya en el almacén.

## Decisión

- **Dónde viven los packs.** `tests/corpus/<proyecto>/` guarda el `pack.yaml`, el `Dockerfile` y un
  `source.toml` con la dirección del repositorio y el nombre completo del commit. No se copia nada
  del proyecto.
- **Cómo se ejecutan.** Un test por proyecto clona el repositorio con toda su historia en un
  directorio temporal, ejecuta `dokime env check` en ese commit con el pack de `tests/corpus/` y
  exige `PASS` sin dejar ningún contenedor ni ningún directorio temporal.
- **Un job propio.** Los tests del conjunto de casos se ejecutan en un job de CI llamado `corpus`,
  en paralelo con los demás, en cada pull request y en cada push a `main`. Es una puerta: una pull
  request que rompe un pack no se fusiona. Fuera de ese job, los tests del conjunto de casos solo se
  ejecutan cuando se piden, para que el job de tests y las puertas en una máquina no dependan de la
  red más de lo que dependen hoy.
- **Los entornos del conjunto de casos van fijados.** Cada Dockerfile del conjunto de casos nombra
  su imagen base por su digest e instala cada paquete, con sus dependencias, en una versión exacta,
  de modo que la puerta solo falle por un cambio nuestro o por la red, y no porque se mueva un tag o
  porque una versión nueva de un paquete rompa un test de un proyecto. Mover cualquiera de ellos es
  un cambio deliberado, en su propia pull request.
- **Qué se vigila.** El job escribe su duración y, cuando falla, si la causa fue la red. Las dos
  cosas se revisan tras unos días de uso.

## Base

La [ADR-0041](0041-the-environment-of-a-verified-project-is-a-dockerfile.es.md) registra la imagen
base de un pack y no obliga a fijarla, para que una persona pueda adoptar un proyecto con el
Dockerfile que tiene. Esa regla es sobre los packs de quienes usan el arnés; no impide fijar los
nuestros, que sirven de puerta.

Medido: las tres ejecuciones del 2026-11-15 y lo que trajeron (los clones de GitHub, la imagen
`python:3.13-slim` de Docker Hub, `pytest` y las dependencias de cada proyecto de PyPI). No medido:
la duración con el almacén vacío, que es el caso de un runner nuevo, y con qué frecuencia falla la
red en CI. Razonamiento, sin test: que un job propio evita que un fallo de la red bloquee las demás
puertas, y que unos días de uso bastan para juzgar su coste.

## Alternativas consideradas

- **Ejecutar el conjunto de casos en el job de tests.** Cada pasada de las puertas lo esperaría, y
  un fallo de la red pararía los tests del código.
- **Ejecutarlo solo en `main`, o con una planificación.** Una pull request podría romper un pack y
  fusionarse.
- **Copiar el código de los proyectos en el repositorio.** Es código de otros en nuestro
  repositorio, y un commit fijado dice lo mismo.
- **Dejar sin fijar los packs del conjunto de casos, como permite la ADR-0041.** Una versión nueva
  de `pytest` o un movimiento de `python:3.13-slim` podría poner la puerta en rojo sin ningún cambio
  nuestro y bloquear todas las pull requests hasta que alguien lo mirara.
- **Guardar una caché de los clones y las imágenes entre ejecuciones.** Ahorraría tiempo; se decide
  cuando se conozca la duración.

## Consecuencias

- Una pull request espera también al job `corpus`; puede tardar minutos.
- Un fallo de la red pone el job en rojo sin ningún defecto en el código. Se informa como tal y el
  job se puede volver a ejecutar.
- El ruleset de `main` gana un check obligatorio, `corpus`, que el mantenedor añade en GitHub; la
  lista de checks obligatorios de la hoja de ruta cambia con él.
- Mover una imagen o un paquete fijados necesita una pull request, que es también donde se ve su
  efecto sobre los tres proyectos.
- Un cuarto repositorio del conjunto de casos es un directorio más en `tests/corpus/`.
