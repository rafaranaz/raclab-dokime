# Hoja de ruta

Cada fase tiene criterios de salida. **La siguiente fase no se abre hasta que la anterior los
cumple todos** ([ADR-0003](adr/0003-reglas-verificadas-en-ci.md)). Si un criterio resulta imposible
o equivocado, se cambia aquí en un PR propio y con su razón, no se salta.

## Fase 0 · Forma de trabajo y puertas — en curso

Reglas de trabajo, pipeline de CI y skills de desarrollo, sin código del harness.

Criterios de salida:

- [x] Entorno reproducible: Python fijado, dependencias en `uv.lock`, instalación con `--locked`.
- [x] Puertas de calidad, gobierno, disciplina y auditoría en CI, cada una con requisitos EARS y
  tests ([docs/requirements/repo.md](requirements/repo.md)).
- [x] Forma de trabajo documentada en [CONTRIBUTING.md](../CONTRIBUTING.md).
- [x] ADR de las decisiones de proceso.
- [x] Skills de desarrollo en `.claude/skills/`.
- [x] CI en verde sobre el PR de la fase en GitHub.
- [ ] Protección de `main` activada en GitHub (acción manual, ver abajo).

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

Decisiones a revisar con evidencia, cada una en su ADR: grafo con tree-sitter frente a SCIP, motor
de estados propio frente a uno existente, niveles de verificación formal, alcance del MVP (modos,
lenguajes, dashboard y daemon) e interfaz de entrega independiente de GitHub.

Puertas que se añaden en esta fase, porque dependen de la arquitectura:

- Contratos de importación entre módulos (import-linter), generados a partir del diagrama de
  módulos.
- Validación de los diagramas Mermaid.

Criterios de salida:

- Cada módulo tiene interfaz pública, requisitos EARS de alto nivel y puerta de cierre definidos.
- Los ocho diagramas están en `docs/architecture/` y pasan la validación.
- Los contratos de importación están en CI.
- La arquitectura está aprobada en revisión.

## Fase 2 · Porte módulo a módulo

Un módulo abierto a la vez, cada uno con su ámbito, su rama y su PR, en este orden provisional
(se confirmará al cerrar la Fase 1):

`core` → `graph` → `sandbox` → `gateway` → `verify` → `engine` (solo modo delta) → `spec` →
`delivery` → `interfaces`

Alcance inicial de lenguajes: Python y Java. Go y TypeScript entran cuando el núcleo esté cerrado.

Criterios de salida de cada módulo: los de la definición de terminado de
[CONTRIBUTING.md](../CONTRIBUTING.md#definición-de-terminado-de-un-ámbito).

## Acciones manuales pendientes

Configuración de GitHub que no se puede versionar en el repositorio:

- **Protección de `main`** (Settings → Rules → Rulesets, o Branches): exigir PR para integrar,
  exigir que pasen los checks de CI (`lint, types and tests`, `governance checks`,
  `commits and branch scope`, `dependency audit`), exigir historial lineal y bloquear el push
  forzado y el borrado.
- **Métodos de merge** (Settings → General → Pull Requests): permitir solo *Rebase and merge*.
