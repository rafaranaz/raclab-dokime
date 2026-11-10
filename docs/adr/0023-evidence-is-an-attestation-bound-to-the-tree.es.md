<!-- translation-of: 0023-evidence-is-an-attestation-bound-to-the-tree.md sha256:a09ff7583541ea76 -->
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
- Registra, para cada puerta del flujo, que se ejecutó, que se omitió porque la política la
  declara opcional, que no aplicaba o que no se alcanzó, las dos últimas con un motivo derivado
  mecánicamente del contrato, del nivel del pack o de la puerta que detuvo el flujo.
- Registra el origen de cada comprobación; el contrato y quién lo aprobó; las huellas de la imagen
  con su plataforma, del pack, de la política y del flujo; las semillas; la versión del arnés; el
  agente, el modelo, la forma de pago y el peldaño de adopción; y las decisiones humanas con quién
  las tomó, cómo se estableció esa identidad y si fueron delegadas. De las comprobaciones selladas
  lleva huellas y clases de fallo, nunca valores ni entradas.
- **Lo que no se comprobó es un campo obligatorio**, rellenado mecánicamente.
- Lleva una etiqueta de independencia: autoatestado, verificado en CI, o verificado en CI con un
  segundo aprobador.
- El registro de una ejecución solo crece y cada evento guarda la huella del anterior. Conserva
  las respuestas de las personas, las salidas de los modelos y la lista de tests inestables, de
  modo que una orden de repetición puede volver a ejecutar las puertas desde los artefactos
  guardados sin preguntar a nadie. Las puertas selladas solo se pueden repetir donde está la
  clave.
- Se produce evidencia de toda ejecución terminada, sea cual sea su veredicto, y se atesta igual.
  Un cambio rechazado tiene evidencia y no tiene entrega.
- Una orden propia, que solo depende de los módulos `evidence` y `core`, verifica un fichero de
  evidencia. Comprueba las firmas contra la lista de firmantes permitidos
  ([ADR-0024](0024-approval-attestation-and-commit-are-signed-separately.es.md)), el esquema, que
  la huella del sujeto coincide con el árbol, la cadena del registro, y las puertas contra el
  fichero de flujo. No vuelve a ejecutar nada; eso es la repetición.

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
