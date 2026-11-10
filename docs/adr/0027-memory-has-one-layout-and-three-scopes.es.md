<!-- translation-of: 0027-memory-has-one-layout-and-three-scopes.md sha256:06174a15c3eb79dc -->
# ADR-0027 · La memoria tiene una estructura, dos almacenamientos y tres alcances

**Estado:** propuesta

## Contexto

Lo que sobrevive entre sesiones no debe depender de un resumen escrito por un modelo, y en un
equipo el contexto de una historia no debe mezclarse con el de otra. No existe un estándar
aceptado de memoria para agentes.

## Decisión

- La memoria es un directorio de ficheros Markdown, uno por tema, cada uno con una cabecera:
  fecha, quién lo aprobó y la versión del código contra la que se validó.
- Una estructura, dos almacenamientos: un directorio local sin git para un desarrollador solo, o
  el repositorio para un equipo. La implementación es la misma.
- Tres alcances: **proyecto** (glosario, decisiones, política, pack), compartido; **cambio** (el
  contrato de una historia, sus ejemplos y aclaraciones), en el directorio y la rama de ese cambio;
  **persona** (el estado de la ejecución en curso, las propuestas sin aprobar), local y nunca
  compartido.
- Todo se guarda al momento. La aprobación cambia el estado de un elemento, no decide si se
  guarda. Una propuesta vive en el registro local hasta que alguien la aprueba; solo entonces
  cambia un fichero.
- El estado del trabajo sale del registro, no de un resumen.
- El fichero de contexto para agentes es un bloque pequeño y delimitado con lo que no se puede
  deducir del código.

## Base

Literatura y razonamiento. Ninguna forma de memoria gana siempre, y las memorias curadas por un
agente pueden fallar mucho ([estudio](https://www.alphaxiv.org/abs/2607.26637.md)); los resúmenes
generales del repositorio no mejoran los resultados y cuestan un 20 % más
([estudio](https://arxiv.org/abs/2602.11988)). Un directorio por funcionalidad es como organizan
sus ficheros las herramientas de especificación existentes.

## Alternativas consideradas

- **Lo aprobado, solo en el repositorio.** Rastro más fuerte; deja fuera al desarrollador solo sin
  git. En su lugar, la evidencia etiqueta el caso local como autoatestado.
- **Un resumen de la última sesión escrito por el modelo.** Pierde cosas y arrastra errores.

## Consecuencias

- En almacenamiento local, las aprobaciones no tienen rastro independiente.
- Un fichero por término del glosario y por decisión, para evitar conflictos al integrar.
