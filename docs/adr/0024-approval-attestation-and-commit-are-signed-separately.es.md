<!-- translation-of: 0024-approval-attestation-and-commit-are-signed-separately.md sha256:8d025406c4bc88cc -->
# ADR-0024 · La aprobación, la atestación y el commit se firman por separado

**Estado:** aceptada

## Contexto

Si el arnés firma el commit automáticamente con la clave de la persona, la firma demuestra que la
clave estaba en la máquina, no que la persona revisara nada. "Quién aprobó qué" necesita más.

## Decisión

| Acto | Quién firma | Qué se firma | Qué demuestra |
|---|---|---|---|
| Aprobar el contrato | La persona, con un gesto explícito | La huella del contrato y la de lo mostrado | Que alguien aceptó esos ejemplos como criterio |
| Atestar la verificación | La identidad que ejecutó las puertas | El sobre de la evidencia | Que esas puertas dieron ese veredicto sobre ese sujeto |
| Publicar el cambio | La persona | El commit | Autoría, como hoy |

- La firma pasa por el agente de claves del sistema. El arnés nunca carga una clave privada, y el
  envoltorio, cuando se usa, deniega al agente los sockets de los agentes de claves.
- Aprobar es siempre esta firma, sea cual sea el canal que mostró el contrato. La evidencia
  registra si el gesto estaba forzado, por un agente de claves que pide confirmación en cada uso o
  por una llave física, o no.
- Quién puede firmar aprobaciones y atestaciones es una lista de firmantes permitidos guardada en
  el repositorio, en las rutas protegidas. Solo cambia mediante un pull request.
- Los commits firmados se exigen en las ramas, no en `main`.
- El agente de programación figura como coautor del commit.

## Base

Razonamiento. Firmar a través de un agente de claves es como ya firma git.

## Alternativas consideradas

- **Una sola firma automática para todo.** Ver el contexto.
- **Exigir commits firmados en `main`.** GitHub no puede firmar los commits de un merge por
  rebase; la evidencia se ata al árbol
  ([ADR-0023](0023-evidence-is-an-attestation-bound-to-the-tree.es.md)).

## Consecuencias

- Aprobar un contrato exige cada vez una acción deliberada.
- Un desarrollador solo firma los tres actos; la evidencia lo etiqueta como autoatestado.
