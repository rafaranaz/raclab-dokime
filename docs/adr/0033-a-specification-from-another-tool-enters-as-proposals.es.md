<!-- translation-of: 0033-a-specification-from-another-tool-enters-as-proposals.md sha256:4de8f8a38a3c98e2 -->
# ADR-0033 · Una especificación de otra herramienta entra como propuestas

**Estado:** aceptada

## Contexto

Algunos usuarios ya escriben especificaciones con otra herramienta antes de conocer esta. Pedirles
que vuelvan a escribir sus requisitos es fricción sin beneficio. Aceptar esas especificaciones
como contratos sería peor: un contrato es lo que una persona aprobó, con ejemplos que deciden
([ADR-0011](0011-contract-of-requirements-and-approved-examples.es.md)).

## Decisión

- Una orden lee una especificación hecha con otra herramienta y convierte sus requisitos en
  requisitos **propuestos** de un contrato.
- Importar no aprueba nada. La persona revisa lo importado, se añaden los ejemplos, y el contrato
  se aprueba con su firma como cualquier otro.
- Cada requisito registra su procedencia: escrito aquí, o importado, con la herramienta y el
  fichero del que vino.
- El formato del contrato sigue siendo el nuestro. Hay un importador por formato externo, fuera
  del módulo que define el contrato.

## Base

El fichero de requisitos de Kiro contiene frases EARS bajo encabezados y ningún ejemplo concreto
con una entrada y una salida esperada; se ha leído en su
[documentación](https://kiro.dev/docs/specs/feature-specs/requirements-first/). Los formatos de
otras herramientas no se han comprobado para esta decisión. Que a una especificación externa le
falte lo que aquí decide un veredicto, y que por eso no pueda ser un contrato, es razonamiento a
partir de ese único caso y del [ADR-0012](0012-examples-are-observations-at-a-boundary.es.md): un
ejemplo necesita una frontera y comparadores de un catálogo cerrado. La decisión es barata de
deshacer: añade un campo y una orden.

## Alternativas consideradas

- **No importar.** El usuario reescribe los requisitos. Cuesta adopción y no protege nada que la
  aprobación no proteja ya.
- **Adoptar un formato externo como contrato.** El que se ha comprobado no tiene ejemplos en una
  frontera, así que la parte que decide seguiría necesitando un formato nuestro.
- **Tratar los requisitos importados como aprobados.** Se aprobaron para otro fin, sin ejemplos y
  sin la firma que aquí constituye una aprobación.

## Consecuencias

- El formato del contrato lleva un campo `source` en cada requisito.
- Los importadores llegan con el bloque F, uno por cada formato que alguien pida.
- Quien usa otra herramienta conserva su texto y aun así tiene que escribir y aprobar ejemplos.
