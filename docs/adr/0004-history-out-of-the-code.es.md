<!-- translation-of: 0004-history-out-of-the-code.md sha256:10e60819fbda68cf -->
# ADR-0004 · La historia vive en git y en los ADR, no en el código

**Estado:** aceptada

## Contexto

En `dokime` el código de producción tenía unas 27.600 líneas de prosa frente a 31.200 de código, y
1.296 referencias a identificadores de tarea. Los comentarios contaban cómo se llegó a cada línea y
remitían a documentos que ya no existían en el repositorio. Auditar qué hacía una función exigía
separar su explicación de su historia.

## Decisión

Los comentarios y docstrings describen qué hace el código y por qué, en presente. La historia (qué
cambió, cuándo y por qué incidente) va en los mensajes de commit y, cuando es una decisión, en un
ADR. `tools/check_history.py` rechaza identificadores de tarea, versiones, fechas, frases de relato
y referencias a ficheros Markdown inexistentes en comentarios y docstrings.

## Alternativas descartadas

- **Una norma de estilo sin comprobación.** No resiste la presión de ir rápido.
- **Prohibir los comentarios largos.** Algunas decisiones locales necesitan explicación; el problema
  no es la longitud sino el texto que cuenta historia en lugar de comportamiento.

## Consecuencias

- El check es heurístico: puede dejar pasar historia escrita sin marcadores reconocibles. La
  revisión del PR cubre ese hueco.
- Para entender por qué algo cambió hay que mirar `git log` o los ADR, no el fichero.
