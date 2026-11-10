<!-- translation-of: 0025-the-interview-works-on-files-and-ends-by-coverage.md sha256:c6b175a060c0a894 -->
# ADR-0025 · La entrevista trabaja sobre ficheros y termina por cobertura

**Estado:** propuesta

## Contexto

Los modelos rara vez preguntan antes de programar, y cuando entrevistan paran pronto: usan de
cuatro a ocho rondas de veinte y descubren una parte pequeña de los requisitos implícitos.
Preguntar ayuda, y un entrevistador guiado por una estructura de categorías descubre mucho más.

## Decisión

- La entrevista es entre el arnés y la persona. El agente de programación no participa.
- Trabaja sobre los ficheros del contrato. El modelo propone ejemplos con su entrada y su salida;
  la persona los aprueba o los corrige. Cada respuesta se escribe al momento, con quién respondió,
  y se enseña el fragmento cambiado para confirmarlo.
- Una pregunta cada vez, con opciones, una recomendada y siempre una respuesta de texto acotado
  con campos fijos.
- **El arnés decide cuándo termina, por cobertura de categorías.** No hay tope por defecto. Cuando
  la persona dice basta, lo pendiente pasa a una sola lista de supuestos que aprobar, con la
  respuesta que sugiere un modelo marcada como delegada.
- Las dudas se clasifican con sesgo hacia preguntar. Una persona puede delegar respuestas en un
  modelo; la delegación se registra y nunca alcanza a la aprobación del contrato.
- Una pregunta es un dato, con las restricciones de los formularios de MCP. Superficies: ficheros
  y terminal; formularios de MCP cuando se entra al arnés desde un editor; un modo sin preguntas
  para CI.

## Base

Literatura. Preguntar sube la corrección del 71 % al 81 % con personas
([ClarifyGPT](https://arxiv.org/abs/2310.10996)); los modelos sin guía descubren como mucho un
tercio de los requisitos implícitos ([ReqElicitGym](https://arxiv.org/abs/2602.18306); sus datos
publicados y su artículo difieren); un entrevistador guiado llega a 0,69 en el mismo banco de
pruebas ([estudio](https://arxiv.org/abs/2605.05828)). Entrevistar sobre el fichero y actualizarlo
tras cada respuesta es lo que hace `clarify` de Spec Kit, con un tope de cinco preguntas.

## Alternativas consideradas

- **Un tope de pocas preguntas.** Las preguntas útiles llegan tarde.
- **Aprobar un documento terminado al final.** Más frío, y más fácil de aprobar sin leer.

## Consecuencias

- No se encontró evidencia de si las personas aprueban los ejemplos con atención; una prueba
  planta un ejemplo erróneo, anunciado en la política, y cuenta.
- Las preguntas que necesitan algo visual no caben en una terminal.
