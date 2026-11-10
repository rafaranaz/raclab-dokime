<!-- translation-of: ROADMAP.md sha256:d16301b6bcc9771f -->
# Hoja de ruta

*Read in [English](ROADMAP.md).*

Cada fase tiene criterios de salida. **La siguiente fase no se abre hasta que la anterior los
cumple todos** ([ADR-0003](adr/0003-rules-enforced-in-ci.es.md)). Si un criterio resulta imposible
o equivocado, se cambia aquí en un PR propio y con su razón, no se salta.

## Fase 0 · Forma de trabajo y puertas — terminada

Reglas de trabajo, pipeline de CI y skills de desarrollo, sin código del harness.

Criterios de salida:

- [x] Entorno reproducible: Python fijado, dependencias en `uv.lock`, instalación con `--locked`.
- [x] Puertas de calidad, gobierno, disciplina y auditoría en CI, cada una con requisitos EARS y
  tests ([docs/requirements/repo.md](requirements/repo.md)).
- [x] Forma de trabajo documentada en [CONTRIBUTING.es.md](../CONTRIBUTING.es.md).
- [x] ADR de las decisiones de proceso.
- [x] Skills de desarrollo en `.claude/skills/`.
- [x] Documentación en inglés y en español, con las traducciones comprobadas en CI.
- [x] CI en verde sobre el PR de la fase en GitHub.
- [x] Protección de `main` aplicada en GitHub (ver abajo).

## Fase 1 · Arquitectura de referencia

La arquitectura del producto, decidida con evidencia. Cada decisión es un ADR que dice en qué se
apoya (literatura, razonamiento o una prueba) y las alternativas consideradas
([ADR-0008](adr/0008-built-new-nothing-is-ported.es.md)). Se entrega en hitos, cada uno un pull
request revisable por separado:

| Hito | Qué entrega | Ámbito |
|---|---|---|
| 1.1 Mapa y decisiones | Qué es el producto y qué afirma, los invariantes, el contexto, las zonas de confianza, los módulos con sus dependencias permitidas, y los ADR 0008 a 0032 | `arch` |
| 1.2 Gobierno alineado | Una comprobación de que cada ADR desde el 0008 dice en qué se apoya; el acuerdo de trabajo alineado con los bloques de la fase 2 | `repo` |
| 1.3 Datos y evidencia | Los formatos del contrato y de los ejemplos, el predicado de la evidencia, el registro y la secuencia de extremo a extremo de un cambio | `arch` |
| 1.4 Estados y flujos | El esquema del fichero de flujo, los estados, las puertas, los presupuestos, la composición por modo y las reglas del validador | `arch` |
| 1.5 Contratos de importación | Las reglas de dependencia del mapa de módulos, comprobadas en CI (import-linter) | `repo` |
| 1.6 Fase cerrada | Criterios de salida marcados e hipótesis listadas con su prueba y su bloque | `arch` |

Datos y evidencia va antes que estados y flujos porque el bloque A depende de los formatos,
mientras que el fichero de flujo no se usa hasta el bloque C. Cada módulo recibe sus requisitos
EARS de alto nivel cuando se abre su ámbito en la fase 2.

Criterios de salida:

- [ ] Los documentos anteriores están en `docs/architecture/` y sus diagramas pasan la validación.
- [ ] Cada ADR desde el 0008 está aceptado o queda expresamente como hipótesis con su prueba.
- [ ] La comprobación de que cada ADR dice en qué se apoya y los contratos de importación están en
  CI.
- [ ] La arquitectura está aprobada en revisión.

## Fase 2 · Construcción por bloques

Siete bloques, cada uno con algo que una persona puede usar y una versión publicada
([ADR-0029](adr/0029-build-order-starts-with-auditing.es.md)). Dentro de un bloque hay un solo
ámbito de módulo abierto a la vez, en el orden indicado. Un bloque se cierra cuando su criterio de
salida, medido sobre el conjunto de casos
([ADR-0030](adr/0030-the-harness-is-measured-on-a-corpus-with-known-verdicts.es.md)), se cumple y
se publica. Un resultado malo también se publica.

| Bloque | Qué puede hacer un usuario al cerrarlo | Módulos, en orden | Criterio de salida | Versión |
|---|---|---|---|---|
| A · Auditar | Verificar un cambio terminado, hecho por cualquier agente, contra un contrato escrito a mano, en local y en CI | `core`, `contract`, `packs`, `sandbox` (entorno de verificación), `verify`, `evidence`, `interfaces` | Ningún falso aprobado en parches que fallan ejemplos visibles, modifican tests o rompen tests existentes | 0.1 |
| B · Reservar | Lo mismo, con ejemplos que el agente no ha visto | `oracle`, `verify`, `bench` | Ningún falso aprobado en las cuatro técnicas de trampa; valor de la reserva medido | 0.2 |
| C · Lanzar | Dar la tarea al arnés y que dirija al agente hasta que el cambio pasa o pregunta | `sandbox` (trabajo), `agents`, `engine` | El mismo cambio completa el circuito con dos perfiles de agente, uno con un modelo de pesos abiertos | 0.3 |
| D · Proteger | Saber qué daña el cambio fuera de lo pedido | `verify` | Las regresiones inyectadas en código cubierto se detectan; tasa de preguntas medida | 0.4 |
| E · Atestar | Entregar evidencia firmada que un tercero verifica sin el arnés | `evidence`, `delivery` | Alguien sin el arnés instalado verifica un fichero de evidencia | 0.5 |
| F · Especificar | Escribir el contrato con ayuda, en español o en inglés | `gateway`, `spec` | Minutos de persona por contrato medidos; prueba de atención hecha | 0.6 |
| G · Generalizar | Usarlo con un segundo lenguaje, con más agentes y en equipo | `packs`, `agents`, `delivery` | El conjunto de casos incluye un repositorio Java; tres agentes distintos completan el circuito | 1.0 |

Los hitos de un bloque se escriben aquí cuando el bloque se abre, y sus números medidos cuando se
cierra. El orden de los bloques B y C se confirma al cerrar el bloque A.

### Hipótesis

Algunas decisiones se apoyan en razonamiento. Cada una tiene una prueba que se hace antes del
bloque que depende de ella, y no se construye sobre una hipótesis fallida sin una decisión nueva.
La lista completa está en el [índice de arquitectura](architecture/README.es.md#hipótesis-por-probar).

| Hipótesis | Prueba | Si falla |
|---|---|---|
| La mayoría de los requisitos reales se pueden expresar como ejemplos en una frontera | A mano, antes de cualquier código del bloque A | Se revisa el formato del contrato antes de construir |
| Aprobar dos o más ejemplos por caso cuesta un tiempo aceptable | A mano, junto con la anterior | Se revisa la regla de reserva |
| Un pack se puede proponer a partir de la configuración de CI de un proyecto | Hito A2, con contenedores y acceso a los registros | Los packs se escriben a mano por proyecto, declarado como coste de adopción |
| La reserva por caso detecta soluciones sobreajustadas | La métrica "valor de la reserva" al cerrar el bloque B | La reserva pasa a ser opcional y el peso va a las relaciones y al bloque D |
| Un agente arranca con su credencial y un directorio de configuración hecho para la ejecución | Dos agentes en Linux y macOS, antes del bloque C | El arnés usa la configuración normal del agente y la evidencia lo dice |
| Un modelo de pesos abiertos completa el circuito | Al cerrar el bloque C | Se publica con qué modelos funciona; la versión no se bloquea |
| Una persona detecta un ejemplo erróneo plantado entre los propuestos | Al cerrar el bloque F | Cambia la forma de presentar los ejemplos antes de cerrar el bloque F |

### Bloque A · Hitos

| Hito | Qué se puede enseñar | Módulos | Se cierra cuando |
|---|---|---|---|
| A0 Pruebas a mano | Tres cambios reales con un contrato escrito a mano y aprobado por una persona, cronometrado; tres repositorios elegidos para el conjunto de casos | Ninguno | Se conocen la proporción de requisitos que caben como ejemplos y los minutos por contrato, y el formato se confirma o se revisa |
| A1 Contrato comprobable | Una orden que valida un contrato y dice qué le falta | `core`, `contract` | Detecta todos los defectos sembrados en contratos de prueba: sintaxis, ejemplos contradictorios, duplicados, requisitos sin ejemplo |
| A2 Entorno reproducible | Una orden que construye la imagen de un proyecto desde su pack y comprueba el pack con la historia del proyecto | `packs`, `sandbox` | Los packs de los tres repositorios se construyen y pasan su autocomprobación |
| A3 Auditoría | Una orden que audita un cambio: línea base, rutas protegidas, ejemplos visibles en las fronteras `cli` y `function`, tests existentes, un veredicto agregado y un fichero de evidencia | `verify`, `evidence`, `interfaces` | El criterio de salida del bloque, sobre los diez primeros casos del conjunto, etiquetados antes de ejecutarlos |
| A4 Auditoría en CI | Un flujo que audita un pull request y adjunta la evidencia, activado en este repositorio; versión 0.1 | `interfaces` | Un pull request real de este repositorio lleva su evidencia |

En el bloque A el conjunto de casos se ejecuta como tests normales del repositorio; `bench` lo
automatiza y calcula las métricas en el bloque B.

Lenguaje inicial: Python. Java llega en el bloque G.

Criterios de salida de cada módulo: la definición de terminado de
[CONTRIBUTING.es.md](../CONTRIBUTING.es.md#definición-de-terminado-de-un-ámbito).

## Configuración de GitHub

Ajustes que viven en GitHub y no se pueden versionar en el repositorio. El repositorio es público,
que es lo que hace que GitHub aplique el ruleset en una cuenta personal.

Un ruleset sobre `main` (Settings → Rules → Rulesets):

- PR obligatorio para integrar, con *Rebase* como único método de merge. No se exige ninguna
  aprobación, porque GitHub no deja a los autores aprobar sus propios PR; mergear es la aprobación.
- Los cuatro checks de CI tienen que pasar (`lint, types and tests`, `governance checks`,
  `commits and branch scope`, `dependency audit`), sobre una rama al día con `main`.
- Historial lineal obligatorio; push forzado y borrado bloqueados.
