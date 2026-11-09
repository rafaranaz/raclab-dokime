# ADR-0002 · Repositorio nuevo y porte módulo a módulo desde `dokime`

**Estado:** aceptada

## Contexto

`dokime` contiene un diseño sólido (los documentos 01 a 08 de su análisis) y mucho conocimiento
nacido de incidentes reales, pero su código no es modular en la práctica:

- 8 ciclos directos entre paquetes y 70 importaciones de funciones privadas entre paquetes.
- El motor antiguo, que se suponía retirado, sigue siendo una dependencia central del nuevo.
- Tanta prosa como código en producción, buena parte contando la historia del propio código.
- El grafo de conocimiento se validó solo sobre ejemplos pequeños; en un repositorio mediano
  resuelve por sorteo una parte de las referencias ambiguas y las marca como seguras.

Cualquier limpieza en sitio obliga a tocar casi todo a la vez, que es el modo de trabajo que llevó
a esa situación.

## Decisión

Se crea `raclab-dokime` vacío, con las fronteras y las puertas definidas antes del primer código.
`dokime` queda como referencia de solo lectura. Cada módulo se porta por separado y solo entra
cuando cumple su definición de terminado: requisitos EARS, tests de comportamiento, sin historia en
el código y respetando las fronteras.

## Alternativas descartadas

- **Limpiar `dokime` en sitio.** Los ciclos y las dependencias privadas hacen que cada paso toque
  varios paquetes a la vez; no hay forma de trabajar un módulo aislado.
- **Reescribir desde cero sin mirar `dokime`.** Perdería el conocimiento incrustado en los gates,
  que nació de fallos reales en ejecuciones de producción.

## Consecuencias

- Durante el porte conviven dos repositorios; `dokime` no recibe cambios.
- Muchos tests de `dokime` fijan detalles internos o la paridad con el motor antiguo. Se porta el
  comportamiento que prueban, no los tests tal cual.
- El orden de porte y los criterios de salida de cada fase están en [ROADMAP](../ROADMAP.md).
