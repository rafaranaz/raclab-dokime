<!-- translation-of: 0009-verification-and-evidence-layer.md sha256:e4d573f4ea37ef4c -->
# ADR-0009 · El producto es una capa de verificación y evidencia alrededor de agentes existentes

**Estado:** aceptada

## Contexto

Los agentes de programación ya escriben código. Lo que está medido como débil es comprobarlo: los
agentes explotan los tests que pueden ver, y una solución que pasa los tests visibles falla a
menudo una suite reservada. Las herramientas revisadas o verifican con un modelo, o atan al
usuario a un proveedor, o estructuran el trabajo sin verificarlo de forma mecánica.

## Decisión

- raclab-dokime no escribe código. Produce un contrato con una persona, entrega el trabajo a un
  agente que el usuario ya tiene y acepta el resultado solo a través de puertas mecánicas.
- Funciona con cualquier agente y cualquier modelo capaz, incluido uno local. La evidencia registra
  el agente y el modelo de cada cambio; compatibilidad no es promesa de resultados iguales.
- Lo que afirma al entregar: *el parche P, sobre el commit B, en el entorno E, cumple el contrato
  C que aprobó la persona X, según las comprobaciones listadas, cada una con su origen; estas
  otras comprobaciones no se hicieron.* No afirma que el cambio sea correcto ni que el contrato
  esté completo.
- Un solo producto sirve a un desarrollador solo y a un equipo regulado. Da a los dos el mismo
  rigor mecánico y etiqueta lo que no puede igualar: si quien aprobó es otra persona.

## Base

Literatura. Los agentes hacen trampa hasta en el 76 % de tareas deliberadamente imposibles
([ImpossibleBench](https://arxiv.org/abs/2510.20270)); la brecha entre tests visibles y reservados
crece con el tamaño de la tarea ([SpecBench](https://arxiv.org/abs/2605.21384)); la verificación
es una categoría de fallo reconocida en sistemas multiagente
([MAST](https://arxiv.org/abs/2503.13657)); un estudio de once agentes encuentra que la
sofisticación del bucle no predice los resultados
([Harness Engineering](https://arxiv.org/abs/2609.00006)). Los dos últimos apoyan la dirección, no
una cifra.

## Alternativas consideradas

- **Construir otro agente de programación.** El bucle no es donde está la debilidad medida.
- **Verificar con un segundo modelo.** Los desarrolladores rechazan más de la mitad de los
  comentarios de revisión automática ([estudio](https://arxiv.org/abs/2607.03316)); un modelo no
  puede ser la puerta.

## Consecuencias

- El producto vale lo que valga el contrato que aprueba una persona; un contrato pobre da una
  conformidad pobre, y se dice así.
- Soportar muchos agentes cuesta un trabajo de integración que una herramienta de un solo agente
  se ahorra.
