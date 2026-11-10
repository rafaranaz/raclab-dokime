<!-- translation-of: 0030-the-harness-is-measured-on-a-corpus-with-known-verdicts.md sha256:7ffffbc90aa989c8 -->
# ADR-0030 · El arnés se mide sobre un conjunto de casos con veredicto conocido

**Estado:** aceptada

## Contexto

Una herramienta cuyo trabajo es no dejar pasar cambios malos tiene que saber cuántos deja pasar.
Los bancos de pruebas públicos no son una vara segura: el de referencia se retiró porque muchos de
sus tests rechazaban soluciones correctas y los modelos habían visto sus datos.

## Decisión

- Un módulo, `bench`, ejecuta el arnés en modo auditoría sobre casos con veredicto conocido:
  parches buenos; parches que fallan ejemplos visibles; parches sobreajustados; las cuatro
  técnicas de trampa medidas (modificar tests, casos especiales, comparación sobrecargada, estado
  entre llamadas); regresiones; un parche bueno en un entorno con un test inestable.
- Métricas: falsos aprobados por etiqueta (la principal), falsos rechazos, tasa de preguntas,
  valor de la reserva (falsos aprobados en parches sobreajustados con y sin ella), estabilidad
  entre dos ejecuciones, minutos de persona por cambio.
- Cada bloque tiene un número como criterio de salida, y los resultados se publican con cada
  versión.
- Tamaño de arranque: unos treinta casos en tres repositorios Python pequeños. Crece con cada
  parche que un agente produzca y una persona etiquete.
- Los puntos fuertes del diseño son invariantes, cada uno con un mecanismo que falla en CI.

## Base

Razonamiento, y la
[auditoría de OpenAI sobre SWE-bench Verified](https://openai.com/index/why-we-no-longer-evaluate-swe-bench-verified/)
para no depender de un banco de pruebas público.

## Alternativas consideradas

- **Criterios de salida cualitativos.** "Funciona" es una impresión.
- **Un banco de pruebas público como vara.** Ver el contexto.

## Consecuencias

- Al principio el conjunto hay que escribirlo a mano.
- Un resultado malo se publica igual.
