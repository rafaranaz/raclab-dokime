<!-- translation-of: 0020-agent-isolation-is-optional-adoption-is-a-ladder.md sha256:8ab0dd69adfdda94 -->
# ADR-0020 · Aislar al agente es opcional; la adopción es una escalera

**Estado:** propuesta

## Contexto

Los desarrolladores ya usan su agente en su propia máquina. Obligar a un contenedor o a un
envoltorio cambia cómo trabajan y rompe a los agentes que necesitan sus herramientas y su red. Las
garantías del producto no salen de dónde corrió el agente.

## Decisión

| Peldaño | Qué cambia para el desarrollador | Qué se obtiene |
|---|---|---|
| 0 · Auditoría en CI | Nada | Verificación completa y evidencia en la petición de integración |
| 1 · Auditoría en local | Una orden antes de subir; un motor de contenedores | Lo mismo antes de subir |
| 2 · El arnés lanza al agente | Una orden en lugar de abrir el agente | El bucle de reintentos con realimentación |
| 3 · Con envoltorio | El agente puede perder herramientas que necesitan la red | Protección de la máquina y de sus credenciales |

- El envoltorio está desactivado salvo que el usuario o la política lo pidan. La copia de trabajo
  también es opcional: el agente puede trabajar en el repositorio del usuario, en una rama, desde
  un árbol limpio.
- **La clave de los ejemplos sellados vive solo en CI.** La máquina de un desarrollador no puede
  descifrarlos, así que su secreto no depende del aislamiento local. Un desarrollador solo sin CI
  guarda la clave en local, y la evidencia lo declara como mejor esfuerzo.
- Cuando el envoltorio está activo, deniega la red local hacia el arnés, y se prueba antes de cada
  lanzamiento.
- La evidencia registra el peldaño y si hubo envoltorio.

## Base

Razonamiento. Los agentes en marcos permisivos actúan fuera de lo pedido entre el 5,4 % y el
27,7 % de las veces ([estudio](https://arxiv.org/abs/2605.18583)), que es el riesgo que cubre el
envoltorio y que el usuario ya asume hoy.

## Alternativas consideradas

- **Envoltorio activado por defecto.** Protege la máquina, pero es toda la fricción y el oráculo
  no lo necesita.
- **Un contenedor obligatorio para el agente.** Habría que soportar cada agente dentro de él.

## Consecuencias

- Sin envoltorio, un agente puede dañar ficheros o leer credenciales en la máquina del usuario.
- Los resultados de lo sellado llegan al subir el cambio, no antes.
