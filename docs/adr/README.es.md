<!-- translation-of: README.md sha256:fad27e64de409a0b -->
# Registro de decisiones (ADR)

*Read in [English](README.md).*

Cada decisión con consecuencias se registra en un ADR: un fichero corto con el contexto, la
decisión, las alternativas descartadas y sus consecuencias. Los ADR aceptados no se editan: si la
decisión cambia, se escribe uno nuevo que sustituye al anterior, o que enmienda una parte, y el
anterior lo dice en su estado. Una decisión aceptada puede cambiar. Cambia cuando hay evidencia y
una razón clara: la nueva mejora lo que existe o resuelve un problema que se encontró. La skill
[adr](../../.claude/skills/adr/SKILL.md) describe el formato.

| Nº | Decisión | Estado |
|---|---|---|
| [0001](0001-record-decisions-in-adrs.es.md) | Registrar las decisiones con ADR | Aceptada |
| [0002](0002-new-repository-ported-by-module.es.md) | Repositorio nuevo, portado módulo a módulo | Sustituida por el 0008 |
| [0003](0003-rules-enforced-in-ci.es.md) | Las reglas se verifican en CI; las skills solo guían | Aceptada |
| [0004](0004-history-out-of-the-code.es.md) | La historia vive en git y en los ADR, no en el código | Aceptada |
| [0005](0005-languages.es.md) | Inglés en el código, documentación bilingüe y producto bilingüe | Aceptada |
| [0006](0006-linear-history-and-closed-scopes.es.md) | Historial lineal con rebase y ámbitos de commit cerrados | Aceptada |
| [0007](0007-mit-license.es.md) | Licencia MIT | Aceptada |
| [0008](0008-built-new-nothing-is-ported.es.md) | El producto se construye nuevo; no se porta nada | Aceptada |
| [0009](0009-verification-and-evidence-layer.es.md) | El producto es una capa de verificación y evidencia alrededor de agentes existentes | Aceptada |
| [0010](0010-threat-model.es.md) | El modelo de amenazas dice qué se defiende y qué no | Aceptada |
| [0011](0011-contract-of-requirements-and-approved-examples.es.md) | Un contrato son requisitos EARS más ejemplos aprobados por una persona | Aceptada |
| [0012](0012-examples-are-observations-at-a-boundary.es.md) | Un ejemplo es una observación en una frontera, comparada fuera del proceso del sujeto | Aceptada |
| [0013](0013-provenance-decides-what-a-check-can-do.es.md) | El origen de una comprobación decide qué puede hacer su fallo | Aceptada |
| [0014](0014-hidden-checks-are-held-out-approved-examples.es.md) | Las comprobaciones ocultas son ejemplos aprobados y reservados por caso, más relaciones aprobadas | Aceptada |
| [0015](0015-a-gate-returns-one-of-four-verdicts.es.md) | Una puerta devuelve uno de cuatro veredictos | Aceptada |
| [0016](0016-verification-in-a-container-on-base-plus-patch.es.md) | La verificación corre en un contenedor sin red, sobre el commit base más el parche | Aceptada, enmendada por el 0041 |
| [0017](0017-damage-outside-the-change-against-a-baseline.es.md) | El daño fuera del cambio se encuentra comparando con una línea base | Aceptada |
| [0018](0018-the-flow-is-a-state-machine-in-a-yaml-file.es.md) | El flujo es una máquina de estados declarada en un fichero YAML | Aceptada |
| [0019](0019-the-harness-launches-the-installed-agent-through-files.es.md) | El arnés lanza el agente instalado y se comunica con él por ficheros | Aceptada |
| [0020](0020-agent-isolation-is-optional-adoption-is-a-ladder.es.md) | Aislar al agente es opcional; la adopción es una escalera | Aceptada |
| [0021](0021-the-agent-disputes-a-check-instead-of-editing-it.es.md) | El agente impugna una comprobación en vez de modificarla | Aceptada |
| [0022](0022-model-calls-of-the-harness-go-through-a-port.es.md) | Las llamadas del arnés a un modelo pasan por un puerto con tres vías | Aceptada |
| [0023](0023-evidence-is-an-attestation-bound-to-the-tree.es.md) | La evidencia es una atestación in-toto atada al árbol resultante | Aceptada |
| [0024](0024-approval-attestation-and-commit-are-signed-separately.es.md) | La aprobación, la atestación y el commit se firman por separado | Aceptada |
| [0025](0025-the-interview-works-on-files-and-ends-by-coverage.es.md) | La entrevista trabaja sobre ficheros y termina por cobertura | Aceptada |
| [0026](0026-formal-consistency-is-checked-per-requirement.es.md) | La consistencia formal se comprueba por requisito, y sus hallazgos preguntan | Aceptada |
| [0027](0027-memory-has-one-layout-and-three-scopes.es.md) | La memoria tiene una estructura, dos almacenamientos y tres alcances | Aceptada |
| [0028](0028-language-support-is-a-declarative-pack-with-levels.es.md) | El soporte de un lenguaje es un pack declarativo con niveles | Aceptada |
| [0029](0029-build-order-starts-with-auditing.es.md) | El orden de construcción empieza por auditar un cambio que ya existe | Aceptada |
| [0030](0030-the-harness-is-measured-on-a-corpus-with-known-verdicts.es.md) | El arnés se mide sobre un conjunto de casos con veredicto conocido | Aceptada |
| [0031](0031-modules-depend-only-on-core.es.md) | Los módulos dependen solo de core; los adaptadores solo los importa la raíz de composición | Aceptada |
| [0032](0032-bilingual-interaction-signs-what-was-shown.es.md) | La persona trabaja en su idioma, y la aprobación firma lo que se le mostró | Aceptada |
| [0033](0033-a-specification-from-another-tool-enters-as-proposals.es.md) | Una especificación de otra herramienta entra como propuestas | Aceptada |
| [0034](0034-a-state-closes-with-the-aggregated-verdict-of-its-gates.es.md) | Un estado se cierra con el veredicto agregado de sus puertas | Aceptada |
| [0035](0035-the-flow-is-loaded-and-validated-in-core.es.md) | El flujo se carga y se valida en core | Aceptada |
| [0036](0036-a-milestone-may-open-an-increment-of-a-later-module.es.md) | Un hito puede abrir un incremento de un módulo posterior | Aceptada |
| [0037](0037-a-contract-is-read-by-strict-rules-of-its-own.es.md) | Un contrato se lee con reglas estrictas propias, y se informa de todos los problemas | Aceptada |
| [0038](0038-directives-in-a-contract-are-marked-with-a-dollar.es.md) | Las directivas de un contrato se marcan con un signo de dólar | Aceptada, enmendada por el 0039 |
| [0039](0039-what-a-contract-of-the-first-version-may-say.es.md) | Qué puede decir un contrato de la primera versión, y qué decide su comprobación | Aceptada |
| [0040](0040-commands-exit-with-a-code-for-each-verdict.es.md) | Las órdenes salen con un código por cada veredicto | Aceptada |
| [0041](0041-the-environment-of-a-verified-project-is-a-dockerfile.es.md) | El entorno de un proyecto verificado es un Dockerfile, y su pack se prueba a sí mismo | Aceptada, enmendada por el 0043 |
| [0042](0042-a-port-of-the-project-repository-composes-the-trees-that-are-built.es.md) | Un puerto del repositorio del proyecto compone los árboles que se construyen | Aceptada, enmendada por el 0044 |
| [0043](0043-tests-run-only-on-an-engine-that-enforces-the-limits.es.md) | Los tests solo se ejecutan en un motor que impone los límites | Aceptada |
| [0044](0044-the-packs-module-drives-the-self-check-in-an-order-of-its-own.es.md) | El módulo packs dirige la autocomprobación en un orden propio | Aceptada |
