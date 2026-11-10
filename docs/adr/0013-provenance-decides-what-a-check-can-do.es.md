<!-- translation-of: 0013-provenance-decides-what-a-check-can-do.md sha256:8ab85cc4e96a8225 -->
# ADR-0013 · El origen de una comprobación decide qué puede hacer su fallo

**Estado:** propuesta

## Contexto

El principio es que las puertas mecánicas deciden y un modelo nunca. Pero un modelo puede escribir
aquello que la puerta evalúa: un test, una propiedad, una formalización. Entonces la puerta es
mecánica solo de nombre. Los tests escritos por modelos son ruidosos: en un estudio, el 62 % de
los tests generados que fallaban eran erróneos ellos mismos; en otro, solo el 56 % de los fallos de
propiedades reportados eran defectos reales.

## Decisión

Toda comprobación lleva su origen, y el origen fija el efecto de un fallo:

| Origen | De dónde sale el resultado esperado | Al fallar |
|---|---|---|
| `human` | Una persona aprobó la entrada y la salida | Falla |
| `derived` | Una relación del catálogo, aprobada por una persona, aplicada mecánicamente | Falla |
| `model` | Un modelo escribió la comprobación o estimó la salida | Pregunta a una persona |
| `existing` | La suite que ya tenía el proyecto | Falla como regresión; se marca aparte |

Un modelo puede **proponer** ejemplos. Pasan a `human` cuando una persona los aprueba. La
puntuación de mutación y la revisión por modelo son información en la evidencia, nunca una puerta.

Una comprobación de origen `model` que pasa es solo información: nunca sostiene un `PASS`. Un
requisito cuyas comprobaciones son todas de origen `model` aparece como no comprobado.

La suite que ya tenía el proyecto cuenta como aprobada por una persona, porque entró por cambios
que una persona aprobó. Eso incluye los tests que un agente escribió en un cambio anterior.

## Base

Literatura. [Tests de un segundo modelo](https://drops.dagstuhl.de/entities/document/10.4230/LIPIcs.ESEM.2026.11),
[pruebas por propiedades con agentes](https://arxiv.org/abs/2510.09907), la puntuación de
mutación de suites generadas predice mal los fallos reales
([estudio](https://arxiv.org/abs/2607.22880)), comentarios de revisión rechazados
([estudio](https://arxiv.org/abs/2607.03316)). Incluso tests curados por personas rechazan
soluciones correctas
([OpenAI sobre SWE-bench Verified](https://openai.com/index/why-we-no-longer-evaluate-swe-bench-verified/)).

## Alternativas consideradas

- **Tratar igual todas las comprobaciones ocultas.** Un test generado y ruidoso rechazaría cambios
  buenos.
- **Prescindir de las comprobaciones escritas por modelo.** Encuentran casos que nadie pensó; como
  preguntas son útiles.

## Consecuencias

- Más preguntas a la persona, acotadas por presupuestos.
- La evidencia enseña cuánto de un veredicto descansa en aprobación humana y cuánto en lo demás.
