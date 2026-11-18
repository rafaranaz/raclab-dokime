<!-- translation-of: 0073-the-key-of-the-hold-out-lives-outside-ci-until-b4.md sha256:2d18c66480193e17 -->
# ADR-0073 · La clave de la reserva vive fuera de CI hasta B4

**Estado:** propuesta

## Contexto

Los ejemplos reservados de un contrato se cifran para una lista de destinatarios
([ADR-0072](0072-the-sealed-store-is-encrypted-with-age-for-a-list-of-recipients.es.md)). La puerta
`sealed-examples` necesita una clave privada para descifrarlos y tiene que ejecutar el código del
cambio para observarlo con ellos. La arquitectura ya dice que "la ejecución sellada solo ocurre
donde está la clave", y que en otro sitio la puerta no es aplicable y la evidencia lo dice
([estados y flujos](../architecture/04-states-and-flows.es.md)). No dice dónde está la clave.

En este repositorio la auditoría de una pull request se ejecuta en un workflow cuyo fichero viene de
la pull request, así que una pull request puede cambiar lo que hace ese workflow
([ADR-0071](0071-the-harness-that-audits-a-pull-request-is-that-of-its-base.es.md)).

La revisión estratégica al cerrar el bloque A comparó las opciones; el mantenedor aprobó esta
recomendación. La sesión que revisa el trabajo la investigó primero; la decisión es del mantenedor.

## Decisión

**La regla.** Una clave que descifra contenido reservado nunca está al alcance de un workflow que
una pull request pueda cambiar.

**El mecanismo de B1 a B3, en uso atendido.**

- **La clave vive en la máquina del mantenedor**, en el directorio de estado del arnés, fuera del
  árbol de trabajo, como prevé la
  [disposición de la memoria](../architecture/03-data-and-evidence.es.md) para "la clave cuando es
  local". Un segundo destinatario, elegido por el mantenedor, guarda su propia clave aparte, para
  que perder una clave no pierda los lotes sellados.
- **El run sellado se hace en local**, antes de la fusión, en la máquina que tiene la clave.
- **En CI la puerta `sealed-examples` no es aplicable**, con el motivo de que la clave no está
  allí.
- **La clave nunca es un secreto del repositorio.**
- **Ejecutar la puerta sellada en CI se decide aparte, en B4**, con una ADR propia. La candidata es
  un workflow disparado por `workflow_run`, que se ejecuta con el fichero de la rama por defecto, y
  la clave como secreto de un entorno restringido a `main`, aceptada solo si el modelo de amenazas
  ([ADR-0010](0010-threat-model.es.md)) acepta el contenedor del sandbox como única barrera entre la
  clave y el código del cambio.

## Base

Comprobado en la documentación de GitHub el 2026-11-18:

- "Any user with write access to your repository has read access to all secrets configured in your
  repository" ([uso seguro](https://docs.github.com/en/actions/reference/security/secure-use)); y,
  "with the exception of `GITHUB_TOKEN`, secrets are not passed to the runner when a workflow is
  triggered from a forked repository"
  ([uso de secretos](https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-secrets)).
- `workflow_run` "will only trigger a workflow run if the workflow file exists on the default
  branch", con `GITHUB_SHA` el "Last commit on default branch" y `GITHUB_REF` la "Default
  branch"; y "Running untrusted code on the `workflow_run` trigger may lead to security
  vulnerabilities"
  ([eventos que disparan workflows](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows)).
- La regla de ramas de un entorno "is matched against the `GITHUB_REF` of the workflow run", y una
  regla para `refs/pull/*/merge` dejaría usarlo a los eventos `pull_request`; con revisores
  obligatorios, un job no accede a los secretos del entorno hasta que uno lo aprueba; en GitHub
  Free, los secretos de un entorno y sus revisores obligatorios solo existen en repositorios
  públicos
  ([despliegues y entornos](https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments)).
  Este repositorio es público.
- GitHub Security Lab pone el código no fiable en un workflow `pull_request`, "isolated in an
  unprivileged environment", y da los secretos a un workflow `workflow_run` aparte que actúa sobre
  sus resultados, con el aviso de que "Artifacts resulting from untrusted PR data are themselves
  untrusted"
  ([prevenir las pwn requests](https://securitylab.github.com/resources/github-actions-preventing-pwn-requests/)).

Buscado y no encontrado: una frase de la documentación de GitHub que diga si las pull requests de
ramas del mismo repositorio reciben sus secretos. La primera frase de arriba lo hace innecesario:
quien puede empujar una rama puede escribir un workflow que los lea.

Razonamiento, sin prueba: que el run sellado necesita a la vez la clave y ejecutar el código del
cambio, justo lo que el patrón de Security Lab separa, así que cualquier run suyo en CI junta las
dos cosas en una máquina con el contenedor como única barrera. La prueba es el modelo de amenazas
de B4.

## Alternativas consideradas

- **La clave como secreto del repositorio, en el workflow de la pull request.** Una pull request
  puede cambiar ese workflow y leer la clave.
- **El run sellado en CI desde B1**, con `workflow_run`, un entorno restringido a `main` y
  revisores obligatorios. Los revisores añaden una puerta humana, pero el código del cambio sigue
  ejecutándose junto a la clave, con el contenedor como única barrera; es el patrón que Security Lab
  desaconseja, y se sopesa en B4 con el modelo de amenazas en lugar de darlo por bueno ahora.
- **Un entorno abierto a `refs/pull/*/merge`.** Da la clave al workflow que la pull request puede
  cambiar.

## Consecuencias

- Cada pull request con ejemplos reservados necesita un paso manual en la máquina del mantenedor, y
  la evidencia de CI no cubre los ejemplos sellados; cómo llega a la pull request el resultado del
  run local se decide cuando `verify` construya la puerta.
- El run sellado depende de que la máquina del mantenedor esté disponible; el segundo destinatario
  cubre la pérdida de la clave, no la ausencia de la persona.
- El ejemplo de evidencia de la [arquitectura](../architecture/03-data-and-evidence.es.md) da el
  motivo "the key lives only in CI", lo contrario de esta decisión; se corrige en el alcance `arch`
  cuando se abra el bloque B.
