<!-- translation-of: 0021-the-agent-disputes-a-check-instead-of-editing-it.md sha256:4a90fdbf2ff05d22 -->
# ADR-0021 · El agente impugna una comprobación en vez de modificarla

**Estado:** aceptada

## Contexto

Un agente suele tocar un test porque cree que está mal, y a veces lo está: una persona puede
aprobar un ejemplo equivocado, e incluso los tests curados rechazan soluciones correctas. Sin una
forma de decirlo, el agente modifica el test o retuerce el código para cumplirlo.

## Decisión

- El agente puede impugnar un ejemplo, un test existente o un fallo de lo sellado ("creo que el
  requisito R se cumple"). Debe citar el requisito o el ejemplo aprobado con el que choca.
- Una impugnación nunca cambia nada. Abre una pregunta a una persona, que entonces ve la
  comprobación.
- Los ejemplos aprobados también se pueden impugnar. Si la persona le da la razón, el contrato se
  enmienda: nueva versión, nueva huella, nueva aprobación.
- Las impugnaciones tienen un presupuesto que pregunta al agotarse, y se cuentan en la evidencia.

## Base

Literatura. Dar al modelo una salida para pedir intervención humana bajó las trampas del 54 % al
9 % en una familia de modelos y mucho menos en otra
([ImpossibleBench](https://arxiv.org/abs/2510.20270)); el 35,5 % de las tareas auditadas de un
banco de pruebas tenía tests que rechazaban soluciones correctas
([OpenAI](https://openai.com/index/why-we-no-longer-evaluate-swe-bench-verified/)).

## Alternativas consideradas

- **Los ejemplos aprobados no se pueden impugnar.** Evita el abuso, y también esconde una
  aprobación hecha por error.
- **Una impugnación validada automáticamente.** Si dos enunciados se contradicen es un juicio
  sobre significado; solo la cita y el formato se pueden comprobar mecánicamente.

## Consecuencias

- Un modelo débil puede impugnar para evitar trabajo; el presupuesto y la cuenta lo acotan.
- Cada impugnación aceptada reinicia la especificación de ese contrato.
