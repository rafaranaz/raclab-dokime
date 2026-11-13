<!-- translation-of: 0043-tests-run-only-on-an-engine-that-enforces-the-limits.md sha256:58c73f3ed1c88a7a -->
# ADR-0043 · Los tests solo se ejecutan en un motor que impone los límites

**Estado:** propuesta

## Contexto

La [ADR-0041](0041-the-environment-of-a-verified-project-is-a-dockerfile.es.md) hace de construir
y ejecutar dos órdenes, cada una elegida entre `docker`, `podman` y `buildah`, y registra como no
comprobado lo que el motor elegido no garantiza aparte de la ausencia de red. Se escribió sin
ningún motor con el que probar. Ahora los tres se han ejecutado sobre el corpus, y `buildah run`
solo garantiza la ausencia de red: el código del proyecto, y en el bloque C el de un agente, se
ejecutaría sin tope de memoria, procesador ni procesos y con la raíz escribible.

## Decisión

- **Ejecutar exige cuatro garantías.** Un motor ejecuta tests solo si su adaptador impone: sin red;
  límites de memoria, procesador y procesos; raíz de solo lectura; y un código de salida que
  distingue un proceso matado desde fuera de uno que terminó por sí mismo. Un motor al que le falta
  una se rechaza para ejecutar, y el rechazo nombra la garantía que falta. Registrarla como no
  comprobada ya no basta para estas cuatro.
- **En la primera versión ejecutan `docker` y `podman`; `buildah` solo construye.** Para construir
  vale cualquiera de los tres.
- **El motor que ejecuta tiene que ver la imagen construida.** Los pares aceptados son `docker` con
  `docker`, `podman` con `podman` y `buildah` con `podman`, que comparten el almacén local de
  imágenes. En la primera versión no se mueven imágenes de un almacén a otro.

Esto enmienda la parte de la ADR-0041 sobre construir y ejecutar. El resto de la ADR-0041 sigue en
pie, incluido lo que un adaptador declara además de estas cuatro.

## Base

Comprobado el 2026-11-12 con docker 29.9.3 (demonio, usuario en el grupo `docker`), podman 5.4.2
(sin root) y buildah 1.39.3 (sin root), sobre la imagen de cachetools construida con su pack.

| | docker | podman | `buildah run` |
|---|---|---|---|
| `--network none`: una conexión se rechaza | sí | sí | sí |
| `--memory 256m --memory-swap 256m`, reservando bloques de 50 MB | matado entre 200 y 250 MB, salida 137 | igual | 600 MB reservados |
| `--pids-limit 64`, arrancando 200 hilos | el 64.º no arranca | igual | arrancan 200 |
| `--cpus 0.5`, cuatro procesos ocupados, segundos de CPU por segundo de reloj | 0,50 | 0,50 | 1,59 (dos CPU) |
| `--read-only` | la raíz no se puede escribir | igual | no existe la opción; la raíz se escribe |
| `exit 3` / orden inexistente / SIGKILL desde fuera | 3 / 127 / 137 | 3 / 127 / 137 | 3 / 1 / 1 |

- Con la máquina en reposo y dos CPU, `--cpus 1` dio 0,98 y 1,00 y sin límite 1,63 y 1,58, en
  docker y podman.
- Con `buildah run`, una ejecución matada desde fuera y una orden que no existe terminan las dos
  con 1, que también es lo que devuelve pytest cuando falla un test. Leer el informe solo las
  separa cuando el informe falta.
- La autocomprobación de cachetools dio los mismos siete testigos de diez en los tres motores, con
  los veinte informes iguales test a test. La elección del motor no cambia el resultado en este
  proyecto; cambia lo que se impone mientras se ejecuta.
- Una imagen construida con `buildah` aparece en `podman images` con el mismo identificador y se
  ejecutó con `podman run --network none --read-only --memory 256m`. `docker images` no la mostró.
- Las señales que se envían desde dentro del contenedor a su PID 1 se ignoran, así que la muerte
  se probó desde fuera.

El programa que carga el contenedor, ejecutado como `python /load.py mem|pids|cpu` con cada límite:

```python
if what == "mem":     # 50 MB blocks, every page touched, up to 600 MB
    blocks = [bytearray(50 * 1024 * 1024) for _ in range(12)]
elif what == "pids":  # up to 200 threads that sleep
    for n in range(1, 201):
        threading.Thread(target=time.sleep, args=(5,), daemon=True).start()
elif what == "cpu":   # 4 busy processes for 4 seconds; children CPU time over wall time
    ...
```

Leído en las fuentes: el manual de `buildah run` tiene `--network`, `--cap-drop` y montajes, y
ninguna opción de memoria, procesador, procesos ni raíz de solo lectura, como ya anotó la
ADR-0041.

No comprobado: otras versiones de los motores, docker sin root, podman con root, macOS y Windows,
donde los motores corren dentro de una máquina virtual. Razonamiento, sin prueba: que hace falta
acotar la ejecución antes del bloque C, cuando se ejecute el código de un agente, y también ya,
porque los tests de un proyecto ejecutan cualquier código que importen.

## Alternativas consideradas

- **Dejar la ADR-0041 como está**, con `buildah run` permitido y las garantías que faltan
  registradas como no comprobadas. La evidencia sería honesta, y aun así una ejecución podría
  llenar la memoria de la máquina de la persona o escribir en la imagen que se prueba.
- **Solo `podman`.** Funciona sin root e impone las cuatro garantías, y dejar fuera `docker`
  excluiría el motor que más gente tiene.
- **Quitar `buildah` del todo.** Construye bien y comparte el almacén con `podman`, así que
  mantenerlo para construir cuesta poco.
- **Mover imágenes entre almacenes** (`podman save` y `docker load`). Permite cualquier par, y
  añade un paso cuyo coste crece con el tamaño de la imagen, para un caso que nadie ha pedido.

## Consecuencias

- En una máquina que solo tiene `buildah`, el arnés puede construir una imagen y no puede ejecutar
  tests.
- Los dos adaptadores de ejecución tienen que probar las cuatro garantías en sus tests, con una
  carga como la de arriba, no leyendo las opciones que pasan.
- La evidencia de una ejecución ya no registra ninguna de las cuatro como no comprobada; sigue
  registrando lo que la ADR-0041 deja a cada adaptador.
- Con `docker`, el demonio corre como root y el informe se escribe como root salvo que el adaptador
  pase el usuario; con `podman`, una ruta relativa en un montaje se toma como el nombre de un
  volumen, así que el adaptador pasa rutas absolutas. Las dos son requisitos de `sandbox`, no de
  esta decisión.
- `buildah` con `docker` se rechaza, aunque los dos estén instalados en la misma máquina.
