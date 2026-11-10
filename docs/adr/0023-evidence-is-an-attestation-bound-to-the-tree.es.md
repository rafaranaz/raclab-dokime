<!-- translation-of: 0023-evidence-is-an-attestation-bound-to-the-tree.md sha256:dad6a939fb12da13 -->
# ADR-0023 · La evidencia es una atestación in-toto atada al árbol resultante

**Estado:** propuesta

## Contexto

La evidencia tiene que poder comprobarla alguien que no se fía del arnés. El repositorio integra
por rebase, y GitHub reescribe los commits al hacerlo, así que el identificador de un commit
cambia al integrar.

## Decisión

- La evidencia es una declaración in-toto en un sobre DSSE, con un tipo de predicado propio
  ("conformidad con un contrato").
- Su sujeto es la **huella del árbol resultante** y la huella del parche, no el commit.
- Registra, para cada puerta del flujo, que se ejecutó, que se omitió con un motivo o que no
  aplicaba; el origen de cada comprobación; el contrato y quién lo aprobó; el entorno; el agente,
  el modelo, la forma de pago y el peldaño de adopción; las decisiones humanas con quién las tomó
  y si fueron delegadas.
- **Lo que no se comprobó es un campo obligatorio**, rellenado mecánicamente.
- Lleva una etiqueta de independencia: autoatestado, verificado en CI, o verificado en CI con un
  segundo aprobador.
- El registro de una ejecución solo crece y cada evento guarda la huella del anterior. Las puertas
  se pueden volver a ejecutar desde los artefactos guardados.
- Una orden que solo depende del módulo de evidencia verifica un fichero de evidencia.

## Base

Prueba propia y práctica documentada. En este repositorio, los commits de una petición de
integración cambiaron de identificador en el merge por rebase y conservaron la misma huella de
árbol. GitHub indica que el merge por rebase añade los commits sin verificación de firma
([documentación](https://docs.github.com/en/authentication/managing-commit-signature-verification/about-commit-signature-verification)).
in-toto, SLSA y Sigstore son los formatos que usan las herramientas existentes
([panorama](https://todogroup.org/blog/2026-07-14-verifiable-provenance-ai-assisted-contributions/)).

## Alternativas consideradas

- **Un formato propio.** Nadie más podría verificarlo con herramientas estándar.
- **Atarla al commit e integrar por squash.** Pierde el historial commit a commit que conserva el
  [ADR-0006](0006-linear-history-and-closed-scopes.es.md).

## Consecuencias

- Los campos del predicado tienen que fijarse antes de que el primer bloque escriba evidencia.
- La integridad de la evidencia no dice nada de la calidad del contrato.
