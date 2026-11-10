<!-- translation-of: README.md sha256:35b3e2e1ffe82585 -->
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
| [glossary.es.md](glossary.es.md) | Los términos en que se apoyan los invariantes y las decisiones |
| [Decisiones](../adr/README.es.md) | ADR 0008 a 0032, cada uno con su base y sus alternativas |

Estados y flujos, y datos y evidencia, llegan en los siguientes pull requests de esta fase
([hoja de ruta](../ROADMAP.es.md)).

## Invariantes

Los puntos fuertes del diseño se escriben como invariantes, cada uno con un mecanismo que falla en
CI cuando se rompe
([ADR-0030](../adr/0030-the-harness-is-measured-on-a-corpus-with-known-verdicts.es.md)).

| Id | Invariante | Lo hace cumplir |
|---|---|---|
| INV-1 | No hay camino desde una salida de modelo hasta un `PASS` o un `FAIL` sin una aprobación humana o una derivación mecánica. Una comprobación de origen `model` que pasa no sostiene nada; la suite que ya tenía el proyecto cuenta como aprobada | El tipo del veredicto lleva el origen; un test de propiedad sobre el agregador |
| INV-2 | El código escrito por el agente nunca corre en un proceso que contenga el valor esperado de un ejemplo reservado. Las entradas de los ejemplos reservados sí entran en la zona de verificación, porque el código tiene que recibirlas | El entorno de verificación pasa a la zona solo entradas y registra qué montó y qué pasó; antes de cada ejecución sellada un test busca en los ficheros, los argumentos y el entorno de la zona una cadena centinela puesta como valor esperado. No ve el contenido transformado a propósito, que es código hostil, fuera del modelo de amenazas |
| INV-3 | Desde el reparto, ningún fichero legible desde donde trabaja el agente contiene contenido reservado en claro. Para un desarrollador solo sin CI es mejor esfuerzo, y la evidencia lo dice | Cada lote sellado lleva una cadena centinela; un test la busca en claro antes de cada lanzamiento del agente y antes de cada ejecución sellada. No ve el contenido transformado a propósito, que es código hostil, fuera del modelo de amenazas |
| INV-4 | El veredicto agregado de un cambio se puede recalcular a partir de base, parche, contrato, imagen y su plataforma, pack, política, flujo, semillas y versión del arnés, todos identificados por huella, junto con lo que el registro guardó de la ejecución: las respuestas de las personas, las salidas de los modelos y la lista de tests inestables. Cuando dos ejecuciones difieren, el resultado es `ASK` | Una orden de repetición recalcula el veredicto desde el registro y los artefactos guardados. Las puertas selladas solo se pueden repetir donde está la clave |
| INV-5 | Todo estado no final tiene puerta de salida; todo bucle tiene presupuesto; agotar un presupuesto lleva a un estado que pregunta a una persona | El validador del fichero de flujo, que comprueba las tres cosas |
| INV-6 | No se entrega nada con un `ERROR` sin resolver, y nadie puede dar uno por bueno | El validador rechaza un flujo con una transición de `ERROR` o de `FAIL` a un estado que entrega; un test de propiedad sobre el agregador |
| INV-7 | Toda puerta del flujo aparece en la evidencia como ejecutada, omitida porque la política la declara opcional, no aplicable, o no alcanzada. Las dos últimas llevan su motivo, derivado mecánicamente | Al construir la evidencia, sus puertas se cotejan con la lista de puertas del fichero de flujo, no solo con el esquema |
| INV-8 | Toda decisión humana es un evento con una identidad y con cómo se estableció esa identidad: firmada, declarada, o a través de un cliente y sin verificar. Toda respuesta delegada está marcada | Una decisión llega al arnés por el canal humano, por una firma o por la forja. Cada una de las tres vías registra la identidad y cómo se estableció; el canal humano añade la marca de delegación |
| INV-9 | Solo `interfaces` importa un adaptador. Ningún otro módulo lo hace | Contratos de importación |
| INV-10 | La evidencia se valida con una orden que solo depende de los módulos `evidence` y `core`, de git y del verificador público del esquema de firma que la evidencia nombra | Un test que instala solo esos dos módulos y ejecuta la orden |

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
| Un pack se puede proponer a partir de la configuración de CI de un proyecto | Repetir nuestra prueba parcial con contenedores y acceso a los registros | A |

## Fuera de la primera versión

Interfaces gráficas, varios repositorios por proyecto, un índice de código con precisión de
compilador, un panel web, verificación formal del código y cambios que no son código de aplicación
(migraciones de datos, infraestructura).
