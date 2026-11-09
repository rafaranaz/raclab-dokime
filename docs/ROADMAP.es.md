<!-- translation-of: ROADMAP.md sha256:50142fb0d265d0a6 -->
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

Revisión crítica del diseño de `dokime` (sus documentos 01 a 08, los incidentes registrados y las
mediciones sobre su código) para fijar la arquitectura de este repositorio. Se entrega en varios
PR del ámbito `arch`, revisables por separado:

1. **Contexto y módulos.** Diagrama de contexto (C4 nivel 1) y diagrama de módulos con las
   dependencias permitidas.
2. **Estados y flujos.** Máquina de estados global, composición por modo y sub-máquina TDD con el
   enrutado de fallos.
3. **Datos y confianza.** Modelo del grafo de código, ledger y trazabilidad, secuencia de una
   historia de punta a punta y fronteras de confianza (sandbox, repositorio no confiable,
   secretos).

Decisiones a revisar con evidencia, cada una en su ADR:

- Grafo de código sobre tree-sitter o sobre SCIP.
- Motor de estados propio o uno existente.
- Niveles de verificación formal.
- Alcance del MVP: modos, lenguajes, dashboard y daemon.
- Interfaz de entrega independiente de GitHub.
- Interacción bilingüe: cómo trabaja el usuario en español o en inglés mientras los artefactos
  internos y los prompts siguen en inglés ([ADR-0005](adr/0005-languages.es.md)).

Puertas que se añaden en esta fase, porque dependen de la arquitectura:

- Contratos de importación entre módulos (import-linter), derivados del diagrama de módulos.
- Validación de los diagramas Mermaid.

Criterios de salida:

- Cada módulo tiene definidos su interfaz pública, sus requisitos EARS de alto nivel y su puerta
  de cierre.
- Los ocho diagramas están en `docs/architecture/` y pasan la validación.
- Los contratos de importación están en CI.
- La arquitectura está aprobada en revisión.

## Fase 2 · Porte módulo a módulo

Un módulo abierto a la vez, cada uno con su ámbito, su rama y su PR, en este orden provisional (se
confirmará al cerrar la Fase 1):

`core` → `graph` → `sandbox` → `gateway` → `verify` → `engine` (solo modo delta) → `spec` →
`delivery` → `interfaces`

Alcance inicial de lenguajes: Python y Java. Go y TypeScript entran cuando el núcleo esté cerrado.

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
