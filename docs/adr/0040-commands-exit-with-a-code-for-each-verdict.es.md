<!-- translation-of: 0040-commands-exit-with-a-code-for-each-verdict.md sha256:914a9231facb42eb -->
# ADR-0040 · Las órdenes salen con un código por cada veredicto

**Estado:** aceptada

## Contexto

El hito A1 entrega la primera orden, `contract check`. Una orden la usan una persona en un
terminal y los scripts y pipelines, que leen su código de salida y a veces su salida. El arnés
tiene cuatro veredictos ([ADR-0015](0015-a-gate-returns-one-of-four-verdicts.es.md)), y la
convención habitual de códigos de salida tiene sitio para tres estados.

## Decisión

- **Códigos de salida.** Una orden sale con el código del veredicto al que llegó:

| Veredicto | Código |
|---|---|
| `PASS` | 0 |
| `FAIL` | 1 |
| `ERROR`, y una línea de órdenes no válida | 2 |
| `ASK` | 3 |

- **Salida de texto.** Los hallazgos van a la salida estándar, uno por línea, como
  `path:line: VERDICT code: message`, y una última línea da el veredicto y las cuentas. Cómo se
  usa la orden, cuando la línea de órdenes no es válida, va a la salida de error.
- **Salida para programas.** `--format json` escribe un documento JSON con el fichero, el
  veredicto y los hallazgos. Otros formatos se añaden cuando algo los necesite.
- **Idioma.** La salida de las órdenes está en inglés. Es una interfaz para herramientas y para
  quien las ejecuta; la interacción en el idioma de la persona del
  [ADR-0032](0032-bilingual-interaction-signs-what-was-shown.es.md) trata de lo que una persona
  aprueba.
- **Biblioteca.** La línea de órdenes se analiza con `argparse`, de la biblioteca estándar.

## Base

Comprobado ejecutando las herramientas:

| Herramienta | Limpio | Hallazgos | No pudo trabajar | Otros estados |
|---|---|---|---|---|
| `grep`, `diff` | 0 | 1 | 2 | — |
| ruff | 0 | 1 | 2 con una opción no válida | — |
| mypy | 0 | 1 | 2 con una opción no válida | — |
| pytest | 0 | 1 | 2 a 4 | 5 cuando no se recogió ningún test, 6 |
| `argparse`, ante un error de uso | — | — | 2 | — |

ruff y mypy escriben sus hallazgos en la salida estándar, uno por línea, como
`file:line: code message`. ruff ofrece doce formatos de salida, entre ellos `json`, `github` y
`sarif`.

Leído en las fuentes: el manual de `gh` documenta 0, 1, 2 para una orden cancelada y 4 cuando la
orden requiere autenticación, un estado que pide algo a una persona y tiene código propio. GitHub
Actions convierte una línea `::error file=…,line=…::message` en una anotación.

Así que la convención es 0 limpio, 1 hallazgos, 2 no pudo trabajar, y una herramienta con un
estado fuera de esos tres le da su propio código. `ASK` es un estado así. Razonamiento, sin
prueba: que un pipeline que mira solo el código de salida no debe dejar pasar una pregunta sin que
nadie la vea. No se ha mirado SARIF.

## Alternativas consideradas

- **`ASK` sale con 0, y una opción lo hace fallar.** Un pipeline que no conoce la opción deja
  pasar las preguntas en silencio.
- **`ASK` sale con 1.** Un script no distingue "arregla el contrato" de "contesta una pregunta".
- **click o typer.** Subcomandos más cómodos, a cambio de una dependencia más que auditar.
- **Los formatos de GitHub o SARIF ya.** Nada los usa hasta que la auditoría corra en CI, en el
  hito A4.

## Consecuencias

- Un script puede ramificar por los cuatro veredictos sin leer la salida.
- Un error de la línea de órdenes y un veredicto `ERROR` comparten el código 2: en los dos la
  herramienta no pudo evaluar.
- Toda orden posterior (`audit`, `evidence verify`) sigue los mismos códigos y el mismo formato de
  línea.
