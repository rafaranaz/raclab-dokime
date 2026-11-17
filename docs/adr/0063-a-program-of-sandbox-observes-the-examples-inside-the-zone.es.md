<!-- translation-of: 0063-a-program-of-sandbox-observes-the-examples-inside-the-zone.md sha256:28438d3845747bd3 -->
# ADR-0063 · Un programa de sandbox observa los ejemplos dentro de la zona y escribe lo que vio en JSON

**Estado:** propuesta

## Contexto

El gate `visible-examples` de A3 ejecuta los ejemplos de un contrato en las fronteras `function` y
`cli` ([ADR-0039](0039-what-a-contract-of-the-first-version-may-say.es.md)). Lo decidido: el arnés
manda a la zona de verificación "la base más el parche filtrado, solo las entradas", la zona
devuelve observaciones, y el arnés compara fuera de ella
([`03-data-and-evidence.es.md`](../architecture/03-data-and-evidence.es.md)); el código bajo prueba
solo recibe las entradas, devuelve una observación serializada como JSON, y cada ejemplo se ejecuta
en un proceso nuevo ([ADR-0012](0012-examples-are-observations-at-a-boundary.es.md)). Nada dice qué
programa ejecuta un ejemplo dentro del contenedor, de qué módulo es, cómo llega allí, con qué
intérprete, ni cómo devuelve lo que vio.

## Decisión

- **El programa es de `sandbox`**, detrás de un puerto propio en `core` que observa los pasos de
  los ejemplos en una imagen y un árbol y da sus observaciones. Es un puerto aparte del del entorno
  de verificación, como el del repositorio auditado está aparte del del repositorio del proyecto,
  para que los adaptadores y los dobles de la autocomprobación conserven el suyo. `verify` arma las
  peticiones y `oracle` compara las observaciones con lo esperado.
- **Entra en el contenedor montado en solo lectura**, con las entradas, en un directorio propio
  como `/dokime/probe`. La imagen no cambia, así que su huella es la que se construyó a partir del
  pack, y nada de lo que se ejecuta durante la construcción puede tocar el programa. La evidencia
  registra la huella del programa.
- **El programa principal se ejecuta con el Python de la imagen y `python -I -S`.** No necesita
  nada de terceros: `-I` deja fuera las variables de Python y el directorio del usuario, y `-S` deja
  fuera `site`, cuyos ficheros `.pth` pueden ejecutar código, y la construcción ejecuta código del
  proyecto (`pip install .`) que podría dejar uno.
- **Cada ejemplo se ejecuta en un proceso nuevo**, un hijo `python -I` que sí tiene las
  site-packages de la imagen, porque el código bajo prueba necesita sus dependencias. El hijo
  importa lo que necesita antes de añadir las rutas del proyecto al final de `sys.path`, para que
  un módulo del proyecto no pueda sustituir a uno que ya cargó. Los pasos de un ejemplo comparten su
  proceso.
- **Cada ejemplo tiene su propio límite de tiempo y su propio directorio de trabajo**, escribible y
  vacío, porque la raíz del contenedor es de solo lectura y una orden en la frontera `cli` escribe
  ficheros. Un ejemplo que se cuelga se observa como uno que llegó a su límite, y los demás siguen.
- **Un contenedor por lado.** Todos los ejemplos de un lado de un gate se ejecutan en un
  contenedor, con el que arranca el programa principal; las garantías de una ejecución
  ([ADR-0043](0043-tests-run-only-on-an-engine-that-enforces-the-limits.es.md)) acotan el conjunto.
- **Las observaciones son un fichero JSON en `/dokime/out`**: por cada paso, lo que da `returns` o
  `raises` en `function`, o `exit`, `stdout`, `stderr` y `files` en `cli`. Un valor devuelto que
  JSON no puede contener se observa como tal, con el nombre de su tipo. El adaptador lee el fichero
  con límites: un límite de tamaño, la ruta abierta sin seguir enlaces, un límite de profundidad, y
  el rechazo de las claves repetidas y de `NaN` o los infinitos. Esa lectura no es la forma
  canónica de la [ADR-0062](0062-a-digest-is-taken-over-a-restricted-canonical-json.es.md): un valor
  devuelto puede tener decimales, que la forma canónica rechaza.

## Base

Leído en el código de los runners de otros:

- HumanEval (`human_eval/execution.py`) ejecuta cada solución en un `multiprocessing.Process`, une
  el prompt, la solución y el test y los ejecuta con `exec` en ese proceso, y devuelve un texto,
  `"passed"`, `"failed: …"` o `"timed out"`, a través de una lista compartida. Su
  `reliability_guard` dice de sí mismo que "no es un sandbox de seguridad".
- EvalPlus (`evalplus/eval/__init__.py`) ejecuta cada solución en un `multiprocessing.Process`,
  llama a `out = fn(*inp)` y lo compara con lo esperado, con `np.allclose` y una tolerancia, en el
  mismo proceso que ejecuta el código bajo prueba; devuelve un estado y una lista de booleanos en
  memoria compartida.
- SWE-bench v3.0.0 ejecuta los tests en un contenedor y toma el resultado del log del ejecutor de
  los tests, por lo que un `conftest.py` del agente puede reescribirlo
  ([BenchJack, sección 3](https://arxiv.org/abs/2605.12673)).

Leído en su código por la sesión que revisa el trabajo, en copias del mismo código en Hugging Face:
HumanEval y EvalPlus como arriba, y el runner oficial de LiveCodeBench
(`lcb_runner/evaluation/testing_util.py`, `run_test`), que ejecuta los casos de un problema en un
proceso con `signal.alarm` por cada caso, dentro de un `multiprocessing.Process` con un límite de
tiempo para el conjunto, y compara en ese proceso. El scorer de LiveCodeBench de
[OpenJarvis](https://open-jarvis.github.io/OpenJarvis/api-reference/openjarvis/evals/scorers/livecodebench)
ejecuta en cambio cada caso en un subproceso propio.

Así que HumanEval, EvalPlus y LiveCodeBench deciden si una solución pasó dentro del proceso del
código bajo prueba, y SWE-bench se fía de lo que ese código escribe en su salida; ninguno mantiene
el valor esperado fuera del proceso del código bajo prueba y compara fuera de él, que es lo que hace
esta decisión.

Leído en resúmenes, no en su código:
[evalscope](https://evalscope.readthedocs.io/en/latest/benchmarks/bigcodebench.html) ejecuta
BigCodeBench en un sandbox de Docker con más de 70 bibliotecas instaladas, y el paquete oficial de
BigCodeBench recomienda un sandbox como Docker sin imponerlo; ejecuta `unittest`.

Buscado y no encontrado: un runner de ejemplos que serialice la observación y la compare fuera de
la zona.

Razonamiento, sin test: que un contenedor por lado y un proceso por ejemplo cumplen la ADR-0012 al
coste de un arranque de contenedor en vez de uno por ejemplo, que para los 13 ejemplos del contrato
de `nextver`, por las ejecuciones de la política y por base y parche, serían más de 50 arranques
para un caso.

## Alternativas consideradas

- **El programa de `verify`**, pasado por la ejecución del entorno de verificación. Mezcla la
  lógica de los gates con código que corre dentro de la zona.
- **El programa declarado por el pack**
  ([ADR-0028](0028-language-support-is-a-declarative-pack-with-levels.es.md)). Sigue siendo código
  que alguien escribe; encaja cuando llegue un segundo lenguaje, en el bloque G.
- **El programa dentro de la imagen**, en una capa del arnés. La huella de la imagen cambia con
  cada versión del arnés, y la imagen se construye dos veces.
- **El programa por la entrada estándar de `python -`.** La entrada estándar es la entrada de la
  frontera `cli`.
- **Un intérprete del arnés, montado.** No puede importar las dependencias construidas para el
  Python de la imagen.
- **La frontera `cli` sin programa**, con el entorno capturando su salida. La ejecución del entorno
  de verificación descarta hoy su salida estándar, y A3 es solo Python.
- **Las observaciones en la salida estándar del contenedor.** El código bajo prueba escribe ahí, y
  podría escribir una observación falsa.
- **Las observaciones con `pickle`.** Cargarlas ejecuta código en el arnés.
- **Un contenedor por ejemplo.** Más aislado, y más de 50 arranques para un caso.

## Consecuencias

- El código bajo prueba se ejecuta en el proceso que lo observa, así que puede reescribir su
  observación, por ejemplo con un `atexit`, o cargar un `.pth` en un hijo; lo que esta decisión
  mantiene fuera de la zona es el valor esperado. Resiste T1 y parte de T2 de la
  [ADR-0010](0010-threat-model.es.md), y no es una defensa contra código hostil.
- `core` gana un puerto, `sandbox` un adaptador y un programa, y `verify` un doble del puerto.
- Las observaciones de la frontera `cli` incluyen los ficheros que una orden escribió en su
  directorio de trabajo, que el programa lee sin seguir enlaces.
- Un segundo lenguaje necesita su propio programa; si lo nombra el pack se decide entonces.
