<!-- translation-of: 0067-a-person-approves-the-contract-before-a-change-is-audited-against-it.md sha256:b5f16963a770a2a2 -->
# ADR-0067 · Una persona aprueba el contrato antes de que se audite un cambio contra él

**Estado:** propuesta

## Contexto

En A3 el contrato de una auditoría sale del commit base, o se le da a `audit` desde fuera del
parche, y nunca del parche, y `.dokime/` está protegido sin excepción (VERIFY-024): un contrato que
trae un parche no se puede distinguir de uno que escribió su agente. El roadmap dejó para antes de
A4 cómo encaja con esa regla la auditoría de una pull request que trae su propio contrato. A4 audita
en CI las pull requests de este repositorio, así que cada una necesita un contrato que haya aprobado
una persona. Las aprobaciones firmadas son del bloque E.

En A4 las pull requests de este repositorio se abren con la cuenta del mantenedor, las abra él o un
agente que trabaja para él, así que GitHub no puede distinguir unas de otras.

## Decisión

**La regla.** Una persona aprueba el contrato antes de que se audite un cambio contra él, y el
agente que hace el cambio no puede tocar el contrato ni aprobarlo. La regla vale en todos los modos
de uso; lo que cambia de un modo a otro es el mecanismo que la cumple.

**El mecanismo en A4, en uso atendido.**

- **Dos pull requests.** El contrato entra en `main` en una pull request propia, en
  `.dokime/changes/<story>/contract.yaml`, y la fusión de esa pull request por el mantenedor es su
  aprobación. El cambio llega en otra pull request, que se audita contra el contrato de su base. Un
  cambio que toca `.dokime/` falla la puerta `protected-paths`, como en A3.
- **El story sale del nombre de la rama** del cambio, `<type>/<scope>-<description>`: el story es la
  descripción. No se toma de la descripción de la pull request, que escribe quien la abre.
- **El resumen del job muestra el story y la huella del contrato** que usó la auditoría, y el
  mantenedor los comprueba antes de fusionar la pull request del cambio.
- **Una pull request que solo añade o cambia ficheros bajo `.dokime/changes/` es una pull request de
  contrato.** No se audita, porque `protected-paths` la rechazaría siempre: su contrato se comprueba
  con `contract check`, y el resumen del job dice `contract pull request: checked, not audited`. Una
  pull request que mezcla `.dokime/` con código se audita, y `protected-paths` la rechaza, como debe.

**El límite.** En A4 las pull requests se abren con la cuenta del mantenedor, así que la fusión
como aprobación y el story de la rama se cumplen por disciplina, no porque GitHub impida otra cosa:
un agente con esa cuenta podría fusionar un contrato o nombrar otra rama. La protección es que el
mantenedor compruebe el story y la huella del contrato antes de fusionar el código. Ni siquiera una
revisión obligatoria lo impediría en A4: los propietarios y los administradores de un repositorio
pueden fusionar sin una revisión aprobada. Cuando el agente
tenga una identidad propia, la misma regla la cumplirá un mecanismo, no la disciplina.

**Mecanismos que la regla admite más adelante**, sin reescribirla:

- una revisión obligatoria de los dueños del código de `.dokime/**`, cuando las pull requests las
  abra una identidad distinta de la del mantenedor;
- la aprobación firmada del bloque E, con el contrato cuya huella coincida con ella;
- en uso semiatendido o desatendido, que no está decidido: un agente revisor distinto del que hizo
  el cambio, sin el contexto de su desarrollo y preferiblemente de otra familia de modelos, bajo una
  política aprobada por una persona.

## Base

Comprobado en la documentación de GitHub:

- Una revisión obligatoria de los dueños del código hace que al menos un dueño apruebe una pull
  request que cambia los ficheros que le pertenecen, y el fichero `CODEOWNERS` se lee de la rama
  base de la pull request
  ([sobre los dueños del código](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners)).
- Un workflow ejecutado por `pull_request` desde un fork recibe un token que solo puede leer, y uno
  ejecutado por `pull_request_target` recibe uno que puede escribir
  ([el token de GitHub](https://docs.github.com/fr/enterprise-server@3.13/actions/reference/github_token-reference)).

- La sesión que revisa el trabajo leyó en la documentación de GitHub, "Approving a pull request with
  required reviews", que "Pull request authors cannot approve their own pull requests", y que los
  propietarios y los administradores de un repositorio pueden fusionar sin una revisión aprobada. Con
  la cuenta del mantenedor, por tanto, ni una revisión obligatoria impediría una fusión, que es el
  límite de arriba.

Razonamiento, sin prueba: que un story sacado de la rama, mostrado con la huella de su contrato en el
resumen del job, basta para que el mantenedor vea que el cambio se auditó contra el contrato que
aprobó. La prueba es la primera pull request de A4 que lleve su evidencia.

## Alternativas consideradas

- **El contrato en la misma pull request que el cambio.** El agente podría escribir el juez de su
  propio cambio; es lo que A3 rechazó.
- **Solo el contrato cuya huella coincida con una aprobación firmada**, la candidata del roadmap.
  Necesita las firmas del bloque E.
- **El story de la descripción de la pull request.** La escribe quien abre la pull request, que
  podría nombrar otro contrato ya aprobado y más fácil de cumplir.
- **Que el contrato haya entrado en `main` después de que se tomara la base de la rama.** Evitaría
  reutilizar un contrato viejo, pero la auditoría necesita el contrato en su base, así que la
  condición no tiene una sola lectura; la comprobación del story y la huella por el mantenedor cubre
  el mismo riesgo en A4.

## Consecuencias

- Cada cambio con contrato son dos pull requests, y el contrato se fusiona primero.
- En A4 la regla se cumple por la disciplina de una persona, y la evidencia dice `self-attested`.
- El mantenedor lee el story y la huella del contrato en el resumen del job antes de cada fusión de
  código.
- Una pull request cuya rama no nombra un story con contrato en su base no se audita contra un
  contrato; cómo lo dice el workflow es un requisito del workflow.
