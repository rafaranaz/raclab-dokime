<!-- translation-of: 0047-only-what-changes-a-boundary-or-is-expensive-to-undo-is-an-adr.md sha256:8431dd89f9819850 -->
# ADR-0047 · Solo es una ADR lo que cambia una frontera o cuesta caro deshacer

**Estado:** propuesta

## Contexto

La skill [adr](../../.claude/skills/adr/SKILL.md) pedía una ADR siempre que "se elige entre
alternativas reales y la elección condiciona el trabajo futuro". Casi cualquier elección cabe en
esa frase. En seis días el repositorio reunió 45 ADR y 1834 líneas de código de producto. El hito
A2 tiene cinco ADR, de 6434 palabras, y ninguna línea del paquete ejecuta todavía `git` ni un
contenedor. Límites, códigos de error y cómo se abre un fichero se decidieron en prosa antes de que
ningún código los probara.

## Decisión

Solo es una ADR una decisión que hace una de estas cosas: cambia un invariante, la frontera de un
módulo, el contrato de un puerto, una dependencia, o una regla de proceso o una puerta de CI; o
cuesta caro deshacerla. Todo lo demás, como el valor de un límite, un código de error, un detalle
de implementación o cómo se abre un fichero, es un requisito EARS de su alcance, con su test, y la
razón de un valor va en el commit que lo fija. Si hay duda, la ADR no se escribe: se pregunta al
mantenedor, con una recomendación. La regla está escrita en la skill adr.

## Base

Contado en el repositorio el 2026-11-14, antes de empezar el esqueleto de A2: las 45 ADR desde el
2026-11-09 hasta la ADR-0045, las palabras de la ADR-0041 a la ADR-0045, las líneas de `src/dokime`,
y que ningún módulo del paquete arranca un proceso. Dos auditorías que leyó el mantenedor, no esta
ADR, encontraron que las ADR se escriben antes de probar, y que 5 de 6 revisiones de una ADR
llegaron dos días o menos después de aceptarla. Razonamiento, sin prueba: que un requisito con su
test guarda un límite o un código mejor que la prosa, porque el test falla cuando el valor deja de
cumplirse. La prueba que confirmaría la regla es el resto de A2: cuántas ADR necesita y cuántas se
revisan.

## Alternativas consideradas

- **Dejar la skill como estaba.** Es lo que llevó a la cuenta de arriba.
- **Un límite de tamaño por ADR.** Una ADR corta sobre un detalle sigue siendo un detalle decidido
  antes de probarlo.
- **Ninguna ADR hasta cerrar un hito.** Vale para el resto de A2 por decisión del mantenedor, y
  como regla bloquearía un cambio de un puerto o de una dependencia que haga falta ya.

## Consecuencias

- Los límites, los códigos y los detalles viven en los requisitos de su alcance, donde un test los
  comprueba. Su historia es la del requisito y la de los commits que lo cambian.
- "Se acepta una limitación conocida" deja de ser un motivo por sí solo: una limitación va en las
  consecuencias de la ADR que la causa, o en un requisito.
- Llegan más preguntas al mantenedor cuando no está claro si una decisión cruza una frontera.
- Una decisión escondida en un requisito que debió ser una ADR solo se detecta en la revisión.
