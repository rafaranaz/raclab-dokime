<!-- translation-of: 0032-bilingual-interaction-signs-what-was-shown.md sha256:e85857cd9f1b3630 -->
# ADR-0032 · La persona trabaja en su idioma, y la aprobación firma lo que se le mostró

**Estado:** propuesta

## Contexto

El [ADR-0005](0005-languages.es.md) fijó que el usuario trabaja en español o inglés mientras los
artefactos internos están en inglés, y dejó la frontera para la arquitectura. El mismo texto en
español cuesta entre un 30 % y un 59 % más de tokens que en inglés, según una medición sobre un
solo pasaje.

## Decisión

- Los ejemplos son datos y no necesitan traducción.
- Los requisitos son canónicos en inglés. A la persona se le muestra una versión en su idioma.
- La aprobación firma la huella del contrato canónico y registra la huella de **lo que se
  mostró**. Una diferencia entre las dos no puede cambiar un veredicto, porque el texto de los
  requisitos no decide.
- Los textos del arnés salen de catálogos de mensajes. Las respuestas libres se guardan como se
  escribieron.

## Base

Razonamiento, más
[una medición del coste en tokens](https://dev.to/savi444/tokens-per-word-gpt-5-vs-claude-vs-gpt-4-measured-across-7-languages-4419),
una fuente débil. No se encontró evidencia de peor calidad con entrada en español.

## Alternativas consideradas

- **Conversar y almacenar en el idioma del usuario.** Los artefactos internos mezclarían idiomas.
- **Traducir sin registrar lo mostrado.** Nadie podría saber después qué texto leyó la persona al
  aprobar.

## Consecuencias

- Cada requisito mostrado necesita un paso de traducción, hecho por un modelo y etiquetado como
  tal.
- Los catálogos de mensajes hay que mantenerlos en dos idiomas.
