<!-- translation-of: README.md sha256:60ab783465a7c62c -->
# Arquitectura de referencia

*Read in [English](README.md).*

raclab-dokime es una **capa de verificación y evidencia** alrededor de los agentes de
programación. No escribe código. Produce un contrato con una persona, entrega el trabajo a un
agente que el usuario ya tiene y acepta el resultado solo a través de puertas mecánicas
([ADR-0009](../adr/0009-verification-and-evidence-layer.es.md)).

## Qué afirma y qué no

Cuando entrega un cambio, afirma:

> El parche P, aplicado sobre el commit B, en el entorno E, cumple el contrato C que aprobó la
> persona X, según las comprobaciones listadas, cada una con su origen. Estas otras comprobaciones
> no se hicieron. Estas decisiones las tomó una persona.

No afirma que el cambio sea correcto, que el contrato esté completo ni que los tests que ya tenía
el proyecto sean de fiar. Cuando quien hizo el cambio y quien lo aprobó son la misma persona, la
evidencia lo dice.

## Documentos

| Documento | Contenido |
|---|---|
| [01-context.es.md](01-context.es.md) | Con quién habla el sistema, y las zonas de confianza |
| [02-modules.es.md](02-modules.es.md) | Módulos, puertos y dependencias permitidas |
| [03-data-and-evidence.es.md](03-data-and-evidence.es.md) | El contrato, el registro, la evidencia y un cambio de extremo a extremo |
| [04-states-and-flows.es.md](04-states-and-flows.es.md) | Qué puede decir un fichero de flujo, qué rechaza el validador, las puertas y los dos flujos iniciales |
| [glossary.es.md](glossary.es.md) | Los términos en que se apoyan los invariantes y las decisiones |
| [Decisiones](../adr/README.es.md) | Cada decisión con su estado; desde el ADR-0008, cada uno dice su base y las alternativas consideradas |

Las fases y los bloques de construcción están en la [hoja de ruta](../ROADMAP.es.md).

## Invariantes

Los puntos fuertes del diseño se escriben como invariantes
([ADR-0030](../adr/0030-the-harness-is-measured-on-a-corpus-with-known-verdicts.es.md)). Cada uno
ha de tener un mecanismo que falla en CI cuando se rompe. "Lo hace cumplir hoy" nombra los
requisitos que lo hacen cumplir hoy, con lo que hacen valer; sus tests son aquellos cuyo marcador
`# SDD-EARS:` los nombra. "Todavía no" dice lo que no está construido y el bloque o el hito de la
[hoja de ruta](../ROADMAP.es.md) que lo trae; R6 da un bloque a lo que apunta a él.

| Id | Invariante | Lo hace cumplir hoy | Todavía no |
|---|---|---|---|
| INV-1 | No hay camino desde una salida de modelo hasta un `PASS` o un `FAIL` sin una aprobación humana o una derivación mecánica. Una comprobación de origen `model` que pasa no sostiene nada; la suite que ya tenía el proyecto cuenta como aprobada | VERIFY-003, VERIFY-004, VERIFY-082, VERIFY-163, CONTRACT-071, EVIDENCE-045, EVIDENCE-062: cada comprobación lleva su origen, y un ejemplo de origen `model` que falla pregunta en vez de fallar | Ninguna salida de un modelo llega al arnés hasta la pasarela, bloque F. El test de propiedad sobre el agregador, R6 |
| INV-2 | El código escrito por el agente nunca corre en un proceso que contenga el valor esperado de un ejemplo reservado. Las entradas de los ejemplos reservados sí entran en la zona de verificación, porque el código tiene que recibirlas | CORE-161, SANDBOX-119, PLATFORM-092: la petición de un ejemplo no lleva nada de lo esperado, el adaptador da la huella del programa que monta, y el lote sellado se abre en memoria | La búsqueda de una cadena centinela puesta como valor esperado, en los ficheros, los argumentos y el entorno de la zona, antes de cada ejecución sellada, R2b de la fase R, porque la ejecución sellada ya existe. No ve el contenido transformado a propósito, que es código hostil, fuera del modelo de amenazas |
| INV-3 | Desde el reparto, ningún fichero legible desde donde trabaja el agente contiene contenido reservado en claro. Para un desarrollador solo sin CI es mejor esfuerzo, y la evidencia lo dice | CONTRACT-091, INTERFACES-160, INTERFACES-172: `contract seal` escribe en el proyecto solo el contrato visible y el lote sellado, y un contrato con un id visible y reservado a la vez es un `ERROR` | La búsqueda de la cadena centinela en claro antes de cada lanzamiento del agente, bloque C, y antes de cada ejecución sellada, R2b de la fase R. No ve el contenido transformado a propósito, que es código hostil, fuera del modelo de amenazas |
| INV-4 | El veredicto agregado de un cambio se puede recalcular a partir de base, parche, contrato, imagen y su plataforma, pack, política, flujo, semillas y versión del arnés, todos identificados por huella, junto con lo que el registro guardó de la ejecución: las respuestas de las personas, las salidas de los modelos y la lista de tests inestables. Cuando dos ejecuciones difieren, el resultado es `ASK` | EVIDENCE-022, EVIDENCE-023, EVIDENCE-027, INTERFACES-187, CORE-122, CORE-123, CORE-135: la evidencia nombra por huella la base, la política, la imagen, el pack y la imagen del cambio, la semilla de las relaciones queda registrada, y el registro es una cadena que se verifica | Una orden de repetición que recalcula el veredicto desde el registro y los artefactos guardados, las puertas selladas solo donde está la clave, R6. El flujo, por huella, llega con el fichero de flujo, bloque C |
| INV-5 | Todo estado no final tiene puerta de salida; todo bucle tiene presupuesto; agotar un presupuesto lleva a un estado que pregunta a una persona | INTERFACES-090, INTERFACES-092: el único flujo es la auditoría, fijo en el código, sin bucles ni presupuestos, y un estado que no da `PASS` termina la ejecución | El validador del fichero de flujo, que comprueba las tres cosas, bloque C, donde se usa por primera vez el fichero de flujo |
| INV-6 | No se entrega nada con un `ERROR` sin resolver, y nadie puede dar uno por bueno | CORE-002, INTERFACES-092, INTERFACES-100, EVIDENCE-020: un `ERROR` gana la agregación y termina la ejecución, y la evidencia dice `delivered` como `false`, porque no se entrega nada | El validador, que rechaza un flujo con una transición de `ERROR` o de `FAIL` a un estado que entrega, bloque C; la entrega, bloque E. El test de propiedad sobre el agregador, R6 |
| INV-7 | Toda puerta del flujo aparece en la evidencia como ejecutada, omitida porque la política la declara opcional, no aplicable, o no alcanzada. Las dos últimas llevan su motivo, derivado mecánicamente | VERIFY-121, VERIFY-122, VERIFY-127, INTERFACES-091, INTERFACES-179, EVIDENCE-040, EVIDENCE-042, EVIDENCE-046, EVIDENCE-087, EVIDENCE-088: toda puerta de la auditoría aparece como ejecutada, no aplicable o no alcanzada, con su motivo, cotejada con la lista fija de puertas de la auditoría | El cotejo de las puertas de la evidencia con la lista de puertas del fichero de flujo, bloque C. Una puerta omitida porque la política la declara opcional, R6 |
| INV-8 | Toda decisión humana es un evento con una identidad y con cómo se estableció esa identidad: firmada, declarada, o a través de un cliente y sin verificar. Toda respuesta delegada está marcada | INTERFACES-171: `contract seal` registra la pregunta y la respuesta de su confirmación, sin identidad. La aprobación de un contrato es la fusión de su pull request (ADR-0067), fuera de dokime | La identidad y cómo se estableció, por una firma y por la forja, bloque E. El canal humano, con la marca de delegación, R6 |
| INV-9 | Solo `interfaces` importa un adaptador. Ningún otro módulo lo hace | REPO-100, REPO-103: los contratos de importación, que nombran todos los módulos del diagrama de módulos | — |
| INV-10 | La evidencia se valida con una orden que solo depende de los módulos `evidence` y `core`, de git y del verificador público del esquema de firma que la evidencia nombra | Nada | Un test que instala solo `evidence` y `core` y ejecuta la orden de validación, bloque E |

## Cómo pasa un cambio

1. **Especificar.** El arnés y la persona escriben el contrato: requisitos y ejemplos aprobados
   ([ADR-0011](../adr/0011-contract-of-requirements-and-approved-examples.es.md),
   [ADR-0025](../adr/0025-the-interview-works-on-files-and-ends-by-coverage.es.md)).
2. **Preparar.** Se construye una imagen con todas las dependencias
   ([ADR-0016](../adr/0016-verification-in-a-container-on-base-plus-patch.es.md)).
3. **Línea base.** Los tests existentes y los ejemplos corren sobre el commit base
   ([ADR-0017](../adr/0017-damage-outside-the-change-against-a-baseline.es.md)).
4. **Aprobar.** La persona aprueba el contrato después de ver la línea base; una parte de los
   ejemplos se sella
   ([ADR-0014](../adr/0014-hidden-checks-are-held-out-approved-examples.es.md)).
5. **Trabajar.** El arnés lanza el agente instalado, o el cambio llega ya hecho
   ([ADR-0019](../adr/0019-the-harness-launches-the-installed-agent-through-files.es.md),
   [ADR-0020](../adr/0020-agent-isolation-is-optional-adoption-is-a-ladder.es.md)).
6. **Verificar.** En un contenedor sin red, sobre el commit base más el parche; la comparación con
   lo esperado ocurre fuera
   ([ADR-0012](../adr/0012-examples-are-observations-at-a-boundary.es.md),
   [ADR-0015](../adr/0015-a-gate-returns-one-of-four-verdicts.es.md)).
7. **Entregar.** Un commit y una atestación firmada
   ([ADR-0023](../adr/0023-evidence-is-an-attestation-bound-to-the-tree.es.md),
   [ADR-0024](../adr/0024-approval-attestation-and-commit-are-signed-separately.es.md)).

## Hipótesis por probar

Cada decisión dice en qué se apoya. Estas se apoyan en razonamiento y necesitan una prueba antes
de contar:

| Hipótesis | Prueba | Bloque |
|---|---|---|
| La reserva por caso detecta soluciones sobreajustadas que los ejemplos visibles no detectan | La métrica "valor de la reserva" | B |
| Una persona detecta un ejemplo erróneo plantado entre los propuestos | Plantarlo, anunciado en la política, y contar | F |
| Aprobar dos o más ejemplos por caso cuesta un tiempo aceptable | Minutos de persona por contrato | A, a mano |
| La mayoría de los requisitos reales se pueden expresar como ejemplos en una frontera | Proporción de requisitos marcados sin ejemplo | A |
| Un agente puede arrancar con su credencial y un directorio de configuración hecho para la ejecución | Probarlo con dos agentes en Linux y macOS | C |
| ~~Un pack se puede proponer a partir de la configuración de CI de un proyecto~~ | **Descartada** por la [ADR-0041](../adr/0041-the-environment-of-a-verified-project-is-a-dockerfile.es.md): el pack lo escribe una persona | — |

## Lo que depende de Python

La primera versión verifica proyectos de Python; Java llega en el bloque G. Estas partes de dokime
suponen Python, y son las primeras a las que llega un segundo lenguaje:

- **El programa que observa los ejemplos**, de cualquier frontera, es un programa de Python,
  `sandbox/observe_program.py`, ejecutado con el `python` de la imagen del proyecto
  (`sandbox/podman.py`). La imagen de un proyecto necesita un intérprete de Python incluso para
  observar una línea de órdenes.
- **La frontera `function`.** El programa que observa los ejemplos en la zona,
  `sandbox/observe_program.py`, importa el objetivo con `importlib`, y `oracle/compare.py` lee una
  excepción como la lee `pytest.raises`.
- **Los tests de un fichero.** `verify/existing.py` asocia cada test con su fichero por la ruta de un
  módulo de Python, la ruta sin `.py` y con `/` como `.`.
- **La configuración de los tests.** `packs/sections.py` lee las secciones de un pack en los formatos
  que usa pytest, TOML e INI.
- **El comparador `$fullmatch`.** Su patrón es una expresión regular de Python
  ([ADR-0039](../adr/0039-what-a-contract-of-the-first-version-may-say.es.md)).

Las puertas que comparan árboles y parches, el registro y la evidencia no dependen del lenguaje del
proyecto. La frontera `cli` tampoco en lo que compara, pero sí en el programa que la ejecuta, como
dice el primer punto. Esto está leído en el código, no probado: todavía no se ha verificado ningún
proyecto en otro lenguaje.

## Fuera de la primera versión

Interfaces gráficas, varios repositorios por proyecto, un índice de código con precisión de
compilador, un panel web, verificación formal del código y cambios que no son código de aplicación
(migraciones de datos, infraestructura).
