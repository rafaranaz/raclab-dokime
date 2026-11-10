<!-- translation-of: 0022-model-calls-of-the-harness-go-through-a-port.md sha256:be3a6d37cabb6326 -->
# ADR-0022 · Las llamadas del arnés a un modelo pasan por un puerto con tres vías

**Estado:** aceptada

## Contexto

El arnés necesita un modelo para la entrevista, para proponer ejemplos y para formalizar
requisitos. Llamar a través del agente instalado no pide nada más al usuario, pero deja lo
generado en el historial de ese agente, que el mismo agente puede leer cuando implementa. La
función de MCP que permite a un servidor pedir texto al modelo del cliente está obsoleta.

## Decisión

- Un puerto con tres adaptadores: una API compatible con OpenAI (que incluye servidores locales),
  una API de fabricante y el agente instalado. Ninguno es el de por defecto; elige la
  configuración, por tarea si se quiere.
- **El contenido reservado nunca pasa por la instalación del agente que implementa**, y tampoco
  los ejemplos de un contrato antes del reparto: el adaptador del agente instalado no se usa para
  proponer ni manejar ejemplos de un contrato que ese agente va a implementar.
- Cada prompt es una plantilla registrada con identificador y huella. Cada respuesta se valida
  contra un esquema, se reintenta una vez y, si no, es un error.
- Todo lo que devuelve un modelo tiene origen `model`
  ([ADR-0013](0013-provenance-decides-what-a-check-can-do.es.md)).

## Base

Literatura y razonamiento. La especificación de MCP del 28 de julio de 2026 declara obsoleto el
*sampling* y recomienda integrar directamente con las API de los proveedores
([registro de cambios](https://modelcontextprotocol.io/specification/2026-07-28/changelog.md)).
Los modelos de pesos abiertos dejan de llamar herramientas cuando hay a la vez herramientas y un
esquema JSON ([estudio](https://www.alphaxiv.org/abs/2606.25605.md)), así que las llamadas
estructuradas no llevan herramientas.

## Alternativas consideradas

- **Siempre a través del agente instalado.** No hace falta clave; menos control del formato y la
  fuga descrita en el contexto.
- **Siempre una API directa.** Exige una clave o un modelo local a un usuario que tiene una
  suscripción.

## Consecuencias

- Tres adaptadores que mantener.
- Un usuario sin clave puede ejecutarlo todo en local salvo la propuesta de ejemplos, a
  no ser que configure un modelo local.
