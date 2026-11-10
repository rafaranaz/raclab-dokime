<!-- translation-of: 0018-the-flow-is-a-state-machine-in-a-yaml-file.md sha256:f2b78a3737b4f093 -->
# ADR-0018 · El flujo es una máquina de estados declarada en un fichero YAML

**Estado:** aceptada

## Contexto

El arnés decide qué viene después: preparar, línea base, aprobar, trabajar, verificar, preguntar,
entregar. Un equipo regulado puede necesitar un flujo distinto del de un desarrollador solo, y un
auditor quiere ver el flujo exacto por el que pasó un cambio.

## Decisión

- El flujo es un fichero YAML con un esquema estricto: estados, la puerta que cierra cada uno, la
  transición para cada veredicto, qué estados son finales y cuáles de esos entregan. Los campos
  desconocidos se rechazan.
- Se valida al cargarlo: todo estado no final tiene puerta; desde todo estado se alcanza uno
  final; todo bucle tiene un presupuesto en la política, y agotarlo lleva a un estado que pregunta
  a una persona; ninguna transición lleva de `ERROR` o de `FAIL` a un estado que entrega.
- **Agotar un presupuesto pregunta a una persona.** Ni rechaza ni sigue por su cuenta.
- El fichero no lleva lógica. Las condiciones viven en las puertas, que son código.
- La huella del flujo forma parte de la evidencia.

## Base

Razonamiento: flexibilidad por proyecto, validación antes de ejecutar y el flujo exacto en la
evidencia. Un estudio sobre flujos de políticas apoya el control determinista con un grafo
validado y congelado ([STAGE](https://arxiv.org/abs/2608.22538)); es un solo estudio, en atención
al cliente, y no demuestra que el grafo tenga que ser un fichero.

## Alternativas consideradas

- **Una tabla de transiciones tipada en código**, llevada a fichero cuando exista un segundo
  flujo. Menos trabajo ahora y las mismas validaciones; se descarta porque se quieren flujos por
  proyecto desde el principio.
- **Un grafo dirigido acíclico de pasos.** No puede expresar el bucle de reintentos.
- **Un estándar de flujos existente.** Traen lenguajes de expresiones, que son la lógica en el
  fichero que esta decisión excluye.

## Consecuencias

- Hay que escribir un cargador, un esquema y un validador antes de que corra el primer flujo.
- La tentación de añadir condiciones al fichero hay que rechazarla cada vez.
