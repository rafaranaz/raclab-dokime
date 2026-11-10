<!-- translation-of: 0014-hidden-checks-are-held-out-approved-examples.md sha256:530e57da9d34e167 -->
# ADR-0014 · Las comprobaciones ocultas son ejemplos aprobados y reservados por caso, más relaciones aprobadas

**Estado:** propuesta

## Contexto

Un oráculo oculto derrota a las soluciones ajustadas a lo visible. "Los mismos ejemplos con otros
valores" exige que alguien sepa la salida correcta para los valores nuevos; si la calcula un
modelo, la puerta decisiva la escribe un modelo que nadie revisa.

## Decisión

- La persona aprueba **todos** los ejemplos. Al aprobar el contrato, el arnés reserva una parte al
  azar, con una semilla guardada en el fichero sellado. La persona no elige cuáles.
- Desde ese reparto, el contenido de los ejemplos reservados existe solo cifrado: las copias en
  claro se quitan de los ficheros del contrato, y el registro guarda su huella, no su contenido.
  Antes del reparto todo el conjunto está en claro donde se especifica el contrato; el
  [ADR-0020](0020-agent-isolation-is-optional-adoption-is-a-ladder.es.md) y el
  [ADR-0022](0022-model-calls-of-the-harness-go-through-a-port.es.md) dicen qué lo protege
  entonces.
- La reserva es por caso: todo caso conserva al menos un ejemplo visible; solo los casos con dos o
  más ejemplos ceden uno a la reserva. Un requisito sin ningún caso repetido no tiene reserva, y
  la evidencia lo dice.
- Una persona puede aprobar además **relaciones** de un catálogo cerrado, dichas en lenguaje llano
  ("el orden de las líneas no cambia el total"). El arnés las aplica mecánicamente a entradas
  nuevas generadas con una semilla registrada.
- Lo sellado solo se ejecuta cuando lo visible pasa. Cada lote sellado lleva un canario: un
  ejemplo con el valor esperado mal a propósito; si pasa, la tubería está rota.
- Nada de lo que se escribe en la sesión de trabajo contiene contenido reservado. Ante un fallo de
  lo sellado, el agente recibe el requisito y la clase de fallo, nunca valores; tampoco los llevan
  la lista de tests en riesgo ni ninguna otra realimentación.
- La salida de una ejecución sellada no se imprime en los registros.

## Base

Literatura y razonamiento. Brechas entre visible y reservado y fallos de composición
([SpecBench](https://arxiv.org/abs/2605.21384)); permitir varios envíos sube las trampas del 33 %
al 38 %, y ocultar tests baja el rendimiento legítimo
([ImpossibleBench](https://arxiv.org/abs/2510.20270)). La regla de reserva por caso es
razonamiento, por medir.

## Alternativas consideradas

- **Variantes con una salida estimada por un modelo.** Ver el contexto.
- **Reserva al azar de una proporción fija.** Puede esconder el único ejemplo que explica un caso.

## Consecuencias

- Hacen falta al menos dos ejemplos por caso para que haya reserva; las tablas de filas lo
  abaratan.
- El agente ya no ve todos los ejemplos: ve todos los requisitos y todos los casos.
