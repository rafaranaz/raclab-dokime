<!-- translation-of: README.md sha256:fef2c3551958d1c6 -->
<!-- translation-of: README.md sha256:7517fc99ee866217 -->
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
| [0020](0020-agent-isolation-is-optional-adoption-is-a-ladder.es.md) | Aislar al agente es opcional; la adopción es una escalera | Aceptada, enmendada por el 0073 |
| [0021](0021-the-agent-disputes-a-check-instead-of-editing-it.es.md) | El agente impugna una comprobación en vez de modificarla | Aceptada |
| [0022](0022-model-calls-of-the-harness-go-through-a-port.es.md) | Las llamadas del arnés a un modelo pasan por un puerto con tres vías | Aceptada |
| [0023](0023-evidence-is-an-attestation-bound-to-the-tree.es.md) | La evidencia es una atestación in-toto atada al árbol resultante | Aceptada |
| [0024](0024-approval-attestation-and-commit-are-signed-separately.es.md) | La aprobación, la atestación y el commit se firman por separado | Aceptada |
| [0025](0025-the-interview-works-on-files-and-ends-by-coverage.es.md) | La entrevista trabaja sobre ficheros y termina por cobertura | Aceptada |
| [0026](0026-formal-consistency-is-checked-per-requirement.es.md) | La consistencia formal se comprueba por requisito, y sus hallazgos preguntan | Aceptada |
| [0027](0027-memory-has-one-layout-and-three-scopes.es.md) | La memoria tiene una estructura, dos almacenamientos y tres alcances | Aceptada |
| [0028](0028-language-support-is-a-declarative-pack-with-levels.es.md) | El soporte de un lenguaje es un pack declarativo con niveles | Aceptada |
| [0029](0029-build-order-starts-with-auditing.es.md) | El orden de construcción empieza por auditar un cambio que ya existe | Aceptada |
| [0030](0030-the-harness-is-measured-on-a-corpus-with-known-verdicts.es.md) | El arnés se mide sobre un conjunto de casos con veredicto conocido | Aceptada, enmendada por el 0081 |
| [0031](0031-modules-depend-only-on-core.es.md) | Los módulos dependen solo de core; los adaptadores solo los importa la raíz de composición | Aceptada |
| [0032](0032-bilingual-interaction-signs-what-was-shown.es.md) | La persona trabaja en su idioma, y la aprobación firma lo que se le mostró | Aceptada |
| [0033](0033-a-specification-from-another-tool-enters-as-proposals.es.md) | Una especificación de otra herramienta entra como propuestas | Aceptada |
| [0034](0034-a-state-closes-with-the-aggregated-verdict-of-its-gates.es.md) | Un estado se cierra con el veredicto agregado de sus puertas | Aceptada |
| [0035](0035-the-flow-is-loaded-and-validated-in-core.es.md) | El flujo se carga y se valida en core | Aceptada |
| [0036](0036-a-milestone-may-open-an-increment-of-a-later-module.es.md) | Un hito puede abrir un incremento de un módulo posterior | Aceptada |
| [0037](0037-a-contract-is-read-by-strict-rules-of-its-own.es.md) | Un contrato se lee con reglas estrictas propias, y se informa de todos los problemas | Aceptada |
| [0038](0038-directives-in-a-contract-are-marked-with-a-dollar.es.md) | Las directivas de un contrato se marcan con un signo de dólar | Aceptada, enmendada por el 0039 |
| [0039](0039-what-a-contract-of-the-first-version-may-say.es.md) | Qué puede decir un contrato de la primera versión, y qué decide su comprobación | Aceptada, enmendada por el 0079 |
| [0040](0040-commands-exit-with-a-code-for-each-verdict.es.md) | Las órdenes salen con un código por cada veredicto | Aceptada |
| [0041](0041-the-environment-of-a-verified-project-is-a-dockerfile.es.md) | El entorno de un proyecto verificado es un Dockerfile, y su pack se prueba a sí mismo | Aceptada, enmendada por el 0043 y el 0060 |
| [0042](0042-a-port-of-the-project-repository-composes-the-trees-that-are-built.es.md) | Un puerto del repositorio del proyecto compone los árboles que se construyen | Aceptada, enmendada por el 0044 |
| [0043](0043-tests-run-only-on-an-engine-that-enforces-the-limits.es.md) | Los tests solo se ejecutan en un motor que impone los límites | Aceptada |
| [0044](0044-the-packs-module-drives-the-self-check-in-an-order-of-its-own.es.md) | El módulo packs dirige la autocomprobación en un orden propio | Aceptada |
| [0045](0045-a-test-report-is-read-by-a-bounded-reader-that-refuses-any-dtd.es.md) | Un informe de tests lo lee un lector acotado que rechaza cualquier DTD | Aceptada |
| [0046](0046-look-at-the-remote-before-starting-or-rewriting-a-branch.es.md) | Mirar el remoto antes de empezar o reescribir una rama | Aceptada |
| [0047](0047-only-what-changes-a-boundary-or-is-expensive-to-undo-is-an-adr.es.md) | Solo es una ADR lo que cambia una frontera o cuesta caro deshacer | Aceptada |
| [0048](0048-requirements-go-up-with-their-first-tests.es.md) | Los requisitos se suben con sus primeros tests | Aceptada |
| [0049](0049-every-pull-request-says-what-it-advances.es.md) | Toda pull request dice qué hace avanzar | Aceptada |
| [0050](0050-an-experiment-enters-the-repository-as-a-test.es.md) | Un experimento entra en el repositorio como un test | Aceptada |
| [0051](0051-the-adapters-that-run-a-program-are-exempt-from-s603.es.md) | Los adaptadores que ejecutan un programa quedan fuera de S603 | Aceptada |
| [0052](0052-the-corpus-runs-in-ci-in-a-job-of-its-own-with-the-network.es.md) | El conjunto de casos se ejecuta en CI en un job propio, con red | Aceptada, enmendada por el 0077 y el 0078 |
| [0053](0053-the-plan-of-work-lives-in-the-repository.es.md) | El plan de trabajo vive en el repositorio | Aceptada |
| [0054](0054-the-policy-is-an-optional-file-of-values.es.md) | La política es un fichero opcional de valores, y la primera versión tiene dos | Aceptada |
| [0055](0055-a-case-of-the-corpus-is-labelled-by-how-it-is-built.es.md) | Un caso del conjunto de casos se etiqueta por cómo se construye, y se confirma antes de ejecutarse | Aceptada, enmendada por el 0057 |
| [0056](0056-the-pack-names-the-configuration-of-its-tests.es.md) | El pack nombra la configuración de sus tests, que queda protegida | Aceptada |
| [0057](0057-the-cases-of-the-corpus-come-from-witnesses-that-fit-a-boundary.es.md) | Los casos del conjunto salen de testigos más allá del segundo, que caben en una frontera | Aceptada, enmendada por el 0061 y el 0074 |
| [0058](0058-existing-tests-runs-the-tests-of-the-base-on-the-code-of-the-patch.es.md) | existing-tests ejecuta los tests de la base sobre el código del parche | Aceptada |
| [0059](0059-a-mixed-file-protects-the-section-that-configures-the-tests.es.md) | Un fichero mixto protege la sección que configura los tests | Aceptada |
| [0060](0060-only-the-tests-make-a-commit-a-candidate-of-the-self-check.es.md) | Solo los tests hacen candidato a un commit de la autocomprobación | Aceptada |
| [0061](0061-the-doctests-of-the-documents-are-tests-of-the-pack.es.md) | Los doctests de los documentos son tests del pack, y los de los docstrings son un límite declarado | Aceptada |
| [0062](0062-a-digest-is-taken-over-a-restricted-canonical-json.es.md) | Una huella se toma sobre un JSON canónico restringido, y un registro con hash se guarda en él | Aceptada |
| [0063](0063-a-program-of-sandbox-observes-the-examples-inside-the-zone.es.md) | Un programa de sandbox observa los ejemplos dentro de la zona y escribe lo que vio en JSON | Aceptada, enmendada por el 0080 |
| [0064](0064-the-evidence-of-a3-is-an-unsigned-statement-with-a-closed-predicate.es.md) | La evidencia de A3 es un statement sin firmar con un predicado cerrado | Aceptada, enmendada por el 0065, el 0066 y el 0069 |
| [0065](0065-the-evidence-of-a3-lists-every-gate-of-the-audit-flow.es.md) | La evidencia de A3 lista todas las puertas del flujo de auditoría, alcanzadas o no | Aceptada |
| [0066](0066-the-untrusted-texts-of-the-evidence-are-bounded.es.md) | Los textos no fiables de la evidencia están acotados | Aceptada |
| [0067](0067-a-person-approves-the-contract-before-a-change-is-audited-against-it.es.md) | Una persona aprueba el contrato antes de que se audite un cambio contra él | Aceptada |
| [0068](0068-the-harness-is-named-by-its-version-and-its-commit.es.md) | El arnés se nombra por su versión y su commit | Aceptada |
| [0069](0069-the-predicate-v0-2-adds-what-a4-records.es.md) | El predicado v0.2 añade lo que registra A4 | Aceptada |
| [0070](0070-the-evidence-of-a-pull-request-goes-in-the-summary-of-its-job.es.md) | La evidencia de una pull request va en el resumen de su job y en un artefacto | Aceptada |
| [0071](0071-the-harness-that-audits-a-pull-request-is-that-of-its-base.es.md) | El arnés que audita una pull request es el de su base | Aceptada |
| [0072](0072-the-sealed-store-is-encrypted-with-age-for-a-list-of-recipients.es.md) | El almacén sellado se cifra con age para una lista de destinatarios | Aceptada |
| [0073](0073-the-key-of-the-hold-out-lives-outside-ci-until-b4.es.md) | La clave de la reserva vive fuera de CI hasta B4 | Aceptada, enmendada por el 0082 |
| [0074](0074-a-witness-is-isolated-when-it-is-a-fix-and-nothing-else.es.md) | Un testigo está aislado cuando es un arreglo y nada más | Aceptada |
| [0075](0075-the-predicate-v0-3-records-the-hold-out.es.md) | El predicado v0.3 registra la reserva | Aceptada |
| [0076](0076-a-relation-runs-on-the-visible-examples-of-its-requirement.es.md) | Una relación se ejecuta sobre los ejemplos visibles de su requisito | Aceptada |
| [0077](0077-the-corpus-does-not-run-on-a-pull-request-that-only-changes-text.es.md) | El corpus no se ejecuta en una pull request que solo cambia texto | Aceptada |
| [0078](0078-the-job-corpus-is-split-into-four-parts-and-a-job-that-gathers-them.es.md) | El job corpus se reparte en cuatro trozos y un job que los reúne | Aceptada |
| [0079](0079-an-example-at-function-may-call-the-methods-of-an-object.es.md) | Un ejemplo en function puede llamar a los métodos de un objeto | Aceptada |
| [0080](0080-each-example-is-observed-in-a-container-of-its-own.es.md) | Cada ejemplo se observa en un contenedor propio | Aceptada |
| [0081](0081-bench-computes-the-metrics-from-the-results-that-the-corpus-writes.es.md) | bench calcula las métricas de los resultados que escribe el corpus | Aceptada |
| [0082](0082-the-sealed-gate-does-not-run-in-ci-in-block-b.es.md) | La puerta sellada no corre en CI en el bloque B | Aceptada |
