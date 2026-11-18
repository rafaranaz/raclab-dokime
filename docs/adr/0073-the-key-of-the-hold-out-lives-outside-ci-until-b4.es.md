<!-- translation-of: 0073-the-key-of-the-hold-out-lives-outside-ci-until-b4.md sha256:b45d23156e93ee5d -->
# ADR-0073 · La clave de la reserva vive fuera de CI hasta B4

**Estado:** aceptada

## Contexto

Los ejemplos reservados de un contrato se cifran para una lista de destinatarios
([ADR-0072](0072-the-sealed-store-is-encrypted-with-age-for-a-list-of-recipients.es.md)). La puerta
`sealed-examples` necesita una clave privada para descifrarlos y tiene que ejecutar el código del
cambio para observarlo con ellos. La arquitectura dice que "la ejecución sellada solo ocurre
donde está la clave", y que en otro sitio la puerta no es aplicable y la evidencia lo dice
([estados y flujos](../architecture/04-states-and-flows.es.md)).

La [ADR-0020](0020-agent-isolation-is-optional-adoption-is-a-ladder.es.md) puso ahí la clave: "La
clave de los lotes sellados vive solo en CI. La máquina de un desarrollador no puede descifrarlos."
Dejaba que un desarrollador solo sin CI guardara la clave en local, con el contenido reservado
descifrado "solo en memoria, nunca se escribe en disco", declarado en la evidencia "como mejor
esfuerzo", y con la evidencia registrando la barrera entre el sitio donde los ejemplos están en
claro y el agente: "otra máquina, el envoltorio, otro usuario del sistema, o ninguna".

En este repositorio CI no es un sitio seguro para la clave: la auditoría de una pull request se
ejecuta en un workflow cuyo fichero viene de la pull request, así que una pull request puede cambiar
lo que hace ese workflow
([ADR-0071](0071-the-harness-that-audits-a-pull-request-is-that-of-its-base.es.md)). Y en el bloque
B el cambio lo escribe un agente en la misma máquina donde entonces estaría la clave.

La revisión estratégica al cerrar el bloque A comparó las opciones; el mantenedor aprobó esta
recomendación. La sesión que revisa el trabajo la investigó primero y encontró que tenía que
enmendar la ADR-0020 y cubrir al agente en la misma máquina; la decisión es del mantenedor.

## Decisión

Esta ADR enmienda la ADR-0020: la clave de los lotes sellados no vive en CI hasta que B4 decida otra
cosa, y las condiciones que la ADR-0020 ponía para un desarrollador sin CI pasan a ser la regla.

**La regla.** Una clave que descifra contenido reservado nunca está al alcance de un workflow que
una pull request pueda cambiar, ni del agente que escribe el cambio, ni del código que se juzga.

**El mecanismo de B1 a B3, en uso atendido.**

- **La identidad es una identidad de age guardada cifrada con una contraseña**: un fichero de age
  cifrado con contraseña, que el binario `age` también lee como fichero de identidad, en el
  directorio de estado del arnés, fuera del árbol de trabajo. Un segundo destinatario, elegido por
  el mantenedor, guarda su propia identidad aparte, para que perder una no pierda los lotes
  sellados.
- **El mantenedor escribe la contraseña en el run sellado.** dokime descifra la identidad y el lote
  sellado solo en memoria, nunca en disco, y la evidencia lo declara como mejor esfuerzo.
- **La identidad nunca entra en el sandbox** donde se ejecuta el código que se juzga.
- **La evidencia registra la barrera entre la clave y el agente**: otra máquina, el envoltorio, otro
  usuario del sistema, una contraseña, o ninguna. La contraseña se añade a la lista de la ADR-0020.
- **El run sellado se hace en local**, antes de la fusión. En CI la puerta `sealed-examples` no es
  aplicable, con el motivo de que la clave no está allí.
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

Comprobado en age y en pyrage el 2026-11-18:

- El README de [age](https://github.com/FiloSottile/age): "If an identity file passed to `-i` is a
  passphrase encrypted age file, it will be automatically decrypted"; y "Passphrase-protected
  identity files are not necessary for most use cases, where access to the encrypted identity file
  implies access to the whole system."
- pyrage 1.4.0 tiene `passphrase.decrypt(ciphertext, passphrase)` y `x25519.Identity.from_str`, así
  que una identidad cifrada con contraseña se puede descifrar en memoria. Su
  `ssh.Identity.from_buffer` no admite contraseña en la 1.4.0: el soporte de claves SSH cifradas se
  fusionó el 27 de septiembre de 2026 ([#159](https://github.com/woodruffw/pyrage/pull/159)),
  después de esa versión, y no está publicado.

Buscado y no encontrado: una frase de la documentación de GitHub que diga si las pull requests de
ramas del mismo repositorio reciben sus secretos. La primera frase de arriba lo hace innecesario:
quien puede empujar una rama puede escribir un workflow que los lea.

Razonamiento, sin prueba:

- Que el run sellado necesita a la vez la clave y ejecutar el código del cambio, justo lo que el
  patrón de Security Lab separa, así que cualquier run suyo en CI junta las dos cosas en una máquina
  con el contenedor como única barrera. La prueba es el modelo de amenazas de B4.
- Que una contraseña protege la clave de un agente que lee el fichero, pero no de un agente que
  corre como el mismo usuario y cambia lo que se ejecutará después, el shell, la instalación del
  arnés o un hook, para capturar la contraseña: el límite que dice el README de age. Otro usuario
  del sistema, u otra máquina, lo quita. La prueba, en B1: un run sellado sin la contraseña no puede
  descifrar, y la evidencia nombra la barrera usada.

## Alternativas consideradas

- **La identidad de otro usuario del sistema**, con el run sellado hecho como ese usuario. El agente
  no puede leer la identidad ni cambiar lo que ese usuario ejecuta, lo que cierra el límite de la
  contraseña; cuesta crear un usuario y un motor de contenedores que corra como él.
- **Otra máquina** para el run sellado. La barrera más fuerte, y el mayor trabajo por cada pull
  request.
- **Una clave SSH cifrada con contraseña.** Reutiliza una clave que el mantenedor ya tiene, pero
  pyrage no la admite en una versión publicada.
- **Un fichero de clave en claro en el directorio de estado.** El agente que escribe el cambio puede
  leerlo.
- **La clave como secreto del repositorio, en el workflow de la pull request.** Una pull request
  puede cambiar ese workflow y leer la clave.
- **El run sellado en CI desde B1**, con `workflow_run`, un entorno restringido a `main` y
  revisores obligatorios. Los revisores añaden una puerta humana, pero el código del cambio sigue
  ejecutándose junto a la clave, con el contenedor como única barrera; es el patrón que Security Lab
  desaconseja, y se sopesa en B4 con el modelo de amenazas en lugar de darlo por bueno ahora.
- **Una llave física mediante un plugin de age.** No se examinó.

## Consecuencias

- La ADR-0020 queda enmendada: en este repositorio la clave no vive en CI, y su consecuencia de que
  "los resultados de lo sellado llegan al subir el cambio" deja de valer: llegan cuando el
  mantenedor hace el run sellado, antes de la fusión.
- Cada pull request con ejemplos reservados necesita un paso manual en la máquina del mantenedor,
  que escribe la contraseña, y la evidencia de CI no cubre los ejemplos sellados; cómo llega a la
  pull request el resultado del run local se decide cuando `verify` construya la puerta.
- La evidencia de un run sellado lleva dos cosas que hoy no lleva, que el descifrado fue de mejor
  esfuerzo y la barrera usada; el predicado las recibe cuando se toque `evidence` en B1.
- La barrera de una contraseña es más débil que otro usuario del sistema frente a un agente que corre
  como el mismo usuario; la evidencia la nombra, para que quien la lea la pueda sopesar.
- El ejemplo de evidencia de la [arquitectura](../architecture/03-data-and-evidence.es.md) da el
  motivo "the key lives only in CI", lo contrario de esta decisión; se corrige en el alcance `arch`
  cuando se abra el bloque B.
