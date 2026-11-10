<!-- translation-of: 0005-languages.md sha256:a0e4c0b82155a796 -->
# ADR-0005 · Inglés en el código, documentación bilingüe y producto bilingüe

**Estado:** aceptada

## Contexto

El equipo trabaja en español. El harness genera y analiza requisitos EARS con las palabras clave
canónicas en inglés (`When`, `While`, `If ... then`, `Where`, `shall`), y los agentes que trabajan
sobre el código rinden mejor y cuestan menos con identificadores, comentarios y prompts en inglés.
Dos idiomas que conviven sin regla obligan a traducir después skills y validadores.

Las personas que usen el harness deberían poder trabajar con él en español o en inglés.

## Decisión

- **El código y todo lo que lo rodea va en inglés**: código fuente, identificadores, comentarios,
  docstrings, mensajes de commit, requisitos EARS, README de los módulos y los ficheros que leen los
  agentes (`CLAUDE.md`, `.claude/skills/`, la plantilla de PR).
- **La documentación para personas va en inglés y en español**: README, CONTRIBUTING, hoja de ruta,
  ADR y arquitectura. El inglés es la fuente. La versión en español vive al lado como
  `<nombre>.es.md` y registra el hash del texto en inglés del que se tradujo;
  `tools/check_translations.py` hace fallar CI cuando un documento cambia sin que se revise su
  traducción.
- **El producto permite al usuario elegir español o inglés** en todo lo que lee o escribe:
  entrevistas, la petición, las preguntas de aclaración, las puertas de aprobación y los informes.
  Los artefactos internos y los prompts a los modelos siguen en inglés. Cómo se implementa esa
  frontera (traducir en el borde o conversar directamente en el idioma elegido) se decide en el
  [ADR-0032](0032-bilingual-interaction-signs-what-was-shown.es.md).

## Alternativas descartadas

- **Documentación solo en español.** Deja fuera a quien no habla español y parte el repositorio en
  dos idiomas sin una regla de qué va dónde.
- **Todo en inglés, producto incluido.** Más simple y más barato, pero no cumple el objetivo de que
  los usuarios hispanohablantes trabajen en su idioma.
- **El español como fuente de la documentación.** La documentación describe código que está en
  inglés y la leen agentes que funcionan mejor en inglés; mantener el inglés como fuente evita
  traducir en las dos direcciones.

## Consecuencias

- Cada cambio de documentación hay que hacerlo dos veces. El check de traducciones hace visible ese
  coste e impide que las versiones diverjan sin que nadie lo note.
- Los ficheros de requisitos y los README de los módulos van solo en inglés, porque son parte del
  código.
- El producto bilingüe añade un requisito a los módulos que hablan con el usuario (entrevistas,
  puertas, informes) que la arquitectura tiene que contemplar desde el principio.
