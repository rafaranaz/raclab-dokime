<!-- translation-of: 0053-the-plan-of-work-lives-in-the-repository.md sha256:aeef12908e1b1f76 -->
# ADR-0053 · El plan de trabajo vive en el repositorio

**Estado:** propuesta

## Contexto

El trabajo del arnés se planea en tres niveles: los bloques y sus criterios de salida, los hitos del
bloque abierto con lo que hay que decidir antes de cada uno, y la orientación estratégica del
mantenedor. Los dos primeros también se guardaban en planes fuera del repositorio, junto a la hoja
de ruta. Desde el 2026-11-11 esos planes se desfasaron del repositorio, porque ninguna sesión de
trabajo ni ninguna puerta de CI los leía: una sesión lee el repositorio, y las puertas solo
comprueban el repositorio. El directorio del cambio y el registro encadenado, planeados para A1, no
se construyeron, y ningún plan del repositorio decía que seguían pendientes.

## Decisión

- **`docs/ROADMAP.md` es la única fuente** de los bloques, los hitos, sus criterios de salida y lo
  que hay que decidir antes de cada uno. Lo que se planea y no está escrito ahí no está planeado.
- **La orientación estratégica del mantenedor es un documento privado**, fuera del repositorio, que
  no repite nada de él: guarda lo que el mantenedor quiere y por qué, no hitos ni criterios.
- **Cerrar un hito actualiza la hoja de ruta**: su nota con lo medido, las hipótesis que resolvió y
  la lista "Still to decide". La skill `close-scope` lo dice.
- **Cerrar un bloque** deja en su informe de cierre un recordatorio de revisar la orientación
  estratégica del mantenedor, que es el único momento en que se encuentran los dos.

## Base

Observado por el mantenedor: los planes guardados fuera del repositorio se separaron de él desde el
2026-11-11, mientras la hoja de ruta, que las sesiones leen y cuyos enlaces y traducción comprueban
las puertas, siguió al día. Leído en el repositorio el 2026-11-15: `core` no tiene directorio del
cambio ni registro, aunque el mapa de módulos da el registro a `core` y el modelo de datos sitúa el
cambio en `.dokime/changes/<story>/`. Razonamiento, sin test: que un plan que ningún lector está
obligado a abrir volverá a desfasarse, y que la revisión al cerrar un bloque basta para mantener al
día la orientación privada.

## Alternativas consideradas

- **Mantener el plan fuera y copiarlo a la hoja de ruta de vez en cuando.** Dos copias, y la que no
  se lee se desfasa; es lo que pasó.
- **Poner también la orientación estratégica en el repositorio.** Guarda las razones de una
  persona, que no son una decisión del proyecto ni son para cualquier lector.
- **Una puerta que compare las dos.** El documento privado no está en el repositorio, así que
  ninguna puerta puede leerlo.

## Consecuencias

- Una sesión que quiera saber qué viene después lee solo la hoja de ruta.
- La hoja de ruta crece con cada hito: su nota, sus números medidos y sus preguntas abiertas.
- Lo que el mantenedor decide en privado llega al trabajo solo cuando se escribe en la hoja de
  ruta.
- Lo planeado y no hecho, como el directorio del cambio y el registro, se escribe en la fila del
  hito que lo necesita.
