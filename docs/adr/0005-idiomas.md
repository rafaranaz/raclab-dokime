# ADR-0005 · Documentación en español; código y requisitos en inglés

**Estado:** propuesta

## Contexto

El equipo trabaja en español. El harness genera y analiza requisitos EARS con las palabras clave
canónicas en inglés (`When`, `While`, `If ... then`, `Where`, `shall`), y los agentes que trabajan
sobre el código rinden mejor con identificadores y comentarios en inglés. En `dokime` convivían los
dos idiomas sin regla, lo que obligó a traducciones posteriores de skills y validadores.

## Decisión

- En español: documentación del repositorio (README, guías, ADR, hoja de ruta, arquitectura) y
  skills de desarrollo.
- En inglés: código, identificadores, comentarios, docstrings, mensajes de commit y requisitos
  EARS.

## Alternativas descartadas

- **Todo en español.** Los requisitos EARS en español no coincidirían con las plantillas que el
  propio harness usará, y el desarrollo dejaría de ejercitar el formato del producto.
- **Todo en inglés.** Haría más costosa la revisión de la documentación de diseño, que es donde se
  toman las decisiones.

## Consecuencias

- Los ficheros de requisitos mezclan idiomas: encabezados en español, requisitos en inglés.
- Las puertas que analizan texto (EARS, historia) solo necesitan reglas para un idioma cada una.
