<!-- translation-of: ROADMAP.md sha256:f935f1f828ed0f4d -->
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
([ADR-0008](adr/0008-built-new-nothing-is-ported.es.md)). Se entrega en varios pull requests del
ámbito `arch`, revisables por separado:

1. **Mapa y decisiones.** Qué es el producto y qué afirma, los invariantes, el contexto, las zonas
   de confianza, los módulos con sus dependencias permitidas, y los ADR 0008 a 0032.
2. **Estados y flujos.** La máquina de estados, su composición por modo, la tubería de
   verificación con sus rutas de fallo y los presupuestos.
3. **Datos y evidencia.** Los formatos del contrato y de los ejemplos, el predicado de la
   evidencia, el registro y la secuencia de extremo a extremo de un cambio.

Cada módulo recibe sus requisitos EARS de alto nivel cuando se abre su ámbito en la fase 2.

Puertas que se añaden en esta fase, porque dependen de la arquitectura:

- Contratos de importación entre módulos (import-linter), derivados del diagrama de módulos.
- Una comprobación de que cada ADR dice en qué se apoya.

Criterios de salida:

- Los documentos anteriores están en `docs/architecture/` y sus diagramas pasan la validación.
- Cada ADR desde el 0008 está aceptado o queda expresamente como hipótesis con su prueba.
- Los contratos de importación están en CI.
- La arquitectura está aprobada en revisión.

## Fase 2 · Construcción por bloques

Seis bloques, cada uno con una orden que alguien puede usar
([ADR-0029](adr/0029-build-order-starts-with-auditing.es.md)). Dentro de un bloque hay un solo
ámbito de módulo abierto a la vez, en el orden indicado. Un bloque se cierra cuando su criterio de
salida, un número medido sobre el conjunto de casos
([ADR-0030](adr/0030-the-harness-is-measured-on-a-corpus-with-known-verdicts.es.md)), se cumple y
se publica.

| Bloque | Módulos, en orden | Criterio de salida |
|---|---|---|
| A · Auditar | `core`, `contract`, `packs`, `sandbox` (entorno de verificación), `verify`, `evidence`, `interfaces` | Ningún falso aprobado en parches que fallan ejemplos visibles, modifican tests o rompen tests existentes |
| B · Reservar | `oracle`, `verify`, `bench` | Ningún falso aprobado en las cuatro técnicas de trampa; valor de la reserva medido |
| C · Lanzar | `sandbox` (trabajo), `agents`, `engine` | El mismo cambio completa el circuito con dos perfiles de agente, uno con un modelo de pesos abiertos |
| D · Proteger | `verify` | Las regresiones inyectadas en código cubierto se detectan; tasa de preguntas medida |
| E · Atestar | `evidence`, `delivery` | Alguien sin el arnés instalado verifica un fichero de evidencia |
| F · Especificar | `gateway`, `spec` | Minutos de persona por contrato medidos; prueba de atención hecha |

Lenguaje inicial: Python. Java es el segundo.

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
