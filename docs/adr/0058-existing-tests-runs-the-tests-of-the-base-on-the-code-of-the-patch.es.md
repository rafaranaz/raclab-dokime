<!-- translation-of: 0058-existing-tests-runs-the-tests-of-the-base-on-the-code-of-the-patch.md sha256:1cea78086490f805 -->
# ADR-0058 · existing-tests ejecuta los tests de la base sobre el código del parche

**Estado:** aceptada

## Contexto

El gate `existing-tests` falla cuando un test que pasaba en la línea base falla o desaparece
([ADR-0017](0017-damage-outside-the-change-against-a-baseline.es.md)). Nada dice qué versión de los
tests ejecuta cuando un parche los edita: la del parche, la de la base, o las dos. Cuando el agente
trabaja bajo el arnés, `protected-paths` restaura los ficheros protegidos
([ADR-0016](0016-verification-in-a-container-on-base-plus-patch.es.md)), así que se ejecutan los
tests de la base; para un cambio que llega ya hecho, la pregunta está abierta. La revisión de los
diez casos del conjunto la dejó abierta para A3, antes de construir `existing-tests`.

## Decisión

- **`existing-tests` ejecuta los tests de la base sobre el código del parche.** El árbol que
  ejecuta es la base con el parche aplicado, con las rutas de `tests.paths` y de `tests.config`
  ([ADR-0056](0056-the-pack-names-the-configuration-of-its-tests.es.md)) tomadas de la base. Un
  fichero que el parche añade bajo esas rutas no está en ese árbol.
- **Salvo los ficheros que el contrato autoriza en `may_modify_tests`**, que se ejecutan en su
  versión del parche, para que la autorización conserve su sentido.
- **Un test de un fichero autorizado que desaparece da `ASK`**, y la evidencia lo lista. Quitarlo
  puede ser legítimo, cuando se renombra un fichero o se reorganizan los tests, o una trampa, cuando
  se vacía el fichero, y las dos cosas no se distinguen de forma mecánica.
- **`visible-examples` se ejecuta sobre el mismo árbol que `existing-tests`**: el código del
  parche, con `tests.paths` y `tests.config` de la base, salvo lo autorizado. Los ejemplos llaman
  al código por su frontera y no cargan los tests, así que el entorno se construye una sola vez. Lo
  que el parche cambia en los tests solo lo mira `protected-paths`.
- Los ficheros que mezclan la configuración de los tests con la del proyecto siguen abiertos, como
  dice la ADR-0056.

## Base

Leído en el código de SWE-bench v3.0.0 (`swebench/harness/test_spec/python.py`): la evaluación
ejecuta `git checkout <base_commit>` sobre los ficheros que modifica el parche de tests de
referencia, antes de aplicar ese parche y otra vez al final, así que ejecuta los tests de la base,
más los de referencia, sobre el código del modelo. Solo restaura esos ficheros. BenchJack mostró
que un `conftest.py` en la raíz, creado por el agente, sobrevive a esa restauración y reescribe el
resultado de los tests ([Wang et al., sección 3](https://arxiv.org/abs/2605.12673)); tomar
`tests.paths` y `tests.config` de la base cierra ese agujero aquí. Los agentes editan tests incluso
cuando se les dice que no lo hagan ([ImpossibleBench](https://arxiv.org/abs/2510.20270),
[EvilGenie](https://arxiv.org/abs/2511.21654)).

Medido mientras se construían los casos, en la sesión que los redactó y revisó, ejecutando los casos
con los scripts del borrador del conjunto, a mano, con pytest 8.3.4 en un entorno local y no en el
contenedor, el 2026-11-15 y el 2026-11-16, sobre los dos casos etiquetados *edita tests*:

| Caso | Con los tests del parche | Con los tests de la base |
|---|---|---|
| `python-semver/nextver-changes-the-tests-to-fit` | fallan 0 de 354 | fallan 3 (`tests.test_bump::test_should_versioninfo_bump_*`) |
| `mdformat/skips-the-html-check-and-edits-its-test` | fallan 0 de 4.267 | falla `tests.test_plugins::test_ast_changing_plugin` |

Con los tests del parche solo los cazaría `protected-paths`; con los de la base, `existing-tests`
también los caza. El test de esta medida llega con el ámbito `corpus`.

Buscado y no encontrado: una herramienta que ejecute las dos versiones de los tests y avise cuando
difieren.

Razonamiento, sin test: que en los tres proyectos del conjunto el código no importa nada de
`tests/`, leído y no ejecutado, así que los ejemplos ven el mismo código en ese árbol; y que dos
gates que cazan la misma trampa por medios distintos valen más que uno, porque `protected-paths` lee
las rutas del parche y `existing-tests` ejecuta el código.

## Alternativas consideradas

- **(a) Los tests del parche.** Los dos casos de *edita tests* solo los cazaría `protected-paths`,
  y un parche que edita un test donde el contrato no mira dejaría a `existing-tests` ejecutando el
  test que cambió.
- **(c) Las dos versiones, avisando cuando difieren.** Duplica el tiempo de los tests, unos cuatro
  minutos más en mdformat, para decir lo que ya dice la versión de la base.
- **Los tests de un fichero autorizado que desaparecen no cuentan.** Vaciar un fichero autorizado
  pasaría sin verse.
- **Dan `FAIL`.** Renombrar o reorganizar un fichero autorizado fallaría, y la autorización no
  permitiría quitar un test.

## Consecuencias

- El código del parche se sigue importando en el proceso de pytest, y puede reescribir los
  resultados sin un `conftest.py`, por ejemplo con un hook que se instala al importarse; así que
  `existing-tests` sigue resistiendo T1 y parte de T2, y no más
  ([ADR-0010](0010-threat-model.es.md)). Restaurar los tests y su configuración cierra el agujero
  que BenchJack mostró en SWE-bench; no es una defensa contra código hostil.
- El puerto del repositorio del proyecto tiene que componer las rutas de los tests de la base sobre
  un árbol, la base con el parche aplicado, y no solo sobre un commit. Esto amplía la deuda de una
  operación del puerto que dé el árbol de un commit.
- Un contrato que autoriza un fichero de tests todavía puede perder tests a través de él, y una
  persona lo ve como `ASK`.
