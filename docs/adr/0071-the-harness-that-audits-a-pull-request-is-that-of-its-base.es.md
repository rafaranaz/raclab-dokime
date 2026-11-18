<!-- translation-of: 0071-the-harness-that-audits-a-pull-request-is-that-of-its-base.md sha256:27a48a4a423a96df -->
# ADR-0071 · El arnés que audita una pull request es el de su base

**Estado:** aceptada

## Contexto

A4 ejecuta `audit` en cada pull request de este repositorio, en un workflow ejecutado por
`pull_request` con permiso solo de lectura
([ADR-0070](0070-the-evidence-of-a-pull-request-goes-in-the-summary-of-its-job.es.md)). El contrato y
el pack de una auditoría ya salen de la base del cambio y nunca del parche
([ADR-0067](0067-a-person-approves-the-contract-before-a-change-is-audited-against-it.es.md),
INTERFACES-075). En este repositorio el arnés es el proyecto: una pull request que cambia dokime
cambia el programa que la audita. Por defecto el workflow extrae el merge commit de la pull request,
así que una pull request así se auditaría con su propio código, y podría darse `PASS`.

El problema lo encontró la sesión que revisa el trabajo; la decisión es del mantenedor.

## Decisión

**La regla.** El código que juzga un cambio nunca sale de ese cambio. El arnés que audita una pull
request es el de su base, como lo son su contrato y su pack.

**El mecanismo en A4, en uso atendido.**

- **El workflow extrae `github.event.pull_request.base.sha` en un directorio propio**, instala dokime
  ahí y lo ejecuta desde ahí.
- **Audita el parche de la pull request**, la diferencia entre su base y su cabeza, contra un
  checkout del proyecto.
- **El commit del arnés en la evidencia es el de la base**
  ([ADR-0068](0068-the-harness-is-named-by-its-version-and-its-commit.es.md)), y el resumen del job lo
  muestra.

**El límite.** El fichero del workflow sigue viniendo de la pull request, porque el evento es
`pull_request`: una pull request podría cambiarlo para que ejecute su propio dokime, o ninguno, y un
workflow que ella cambió puede escribir en el resumen del job lo que quiera, también un commit de la
base y `PASS`. Así que el resumen no puede mostrar que el workflow no se cambió. Lo que el mantenedor
comprueba antes de fusionar es que la pull request no cambia nada bajo `.github/workflows/`; solo
entonces el resumen es fiable. Sin `pull_request_target` esto no tiene mecanismo; se cumple por
disciplina, porque las pull requests se abren con la cuenta del mantenedor.

## Base

Comprobado en la documentación de GitHub: "By default, `actions/checkout` in a `pull_request` workflow
also checks out the pull request's merge commit", mientras que para `pull_request_target` "the
workflow file itself still comes from the default branch"
([securely using pull_request_target](https://docs.github.com/en/actions/reference/security/securely-using-pull_request_target)).

Leído con `gh`, en herramientas de otros que comprueban pull requests con código que una pull request
podría cambiar:

- [TrianaLab/aval, issue #134](https://github.com/TrianaLab/aval/issues/134), cerrada: la CI de una pull request debe cargar su política de confianza
  de la rama base, porque si no "a green PR check would be evidence the PR authored itself".
- [microsoft-365-agents-toolkit, pull request #16697](https://github.com/OfficeDev/microsoft-365-agents-toolkit/pull/16697), fusionada: "Check out the evaluation harness from
  the exact PR base SHA", con el contenido de la pull request superpuesto como datos; se ejecuta en
  `pull_request_target` con un entorno que necesita una aprobación.
- [electrum, pull request #11076](https://github.com/spesmilo/electrum/pull/11076), cerrada sin fusionar: la revisión de seguridad extrae el código de
  confianza de `pull_request.base.sha` y toma la pull request solo como datos de git.

Leído en la misma página de GitHub, y en el relato de un incidente de SafeDep, sobre por qué el
workflow no se ejecuta en `pull_request_target`:

- El job "receives the base repository's GITHUB_TOKEN and access to repository and organization
  secrets".
- La caché está fuera de los permisos del token. En el incidente de TanStack, el 11 de mayo de 2026,
  un workflow en `pull_request_target` escribió una caché envenenada en el ámbito de la rama por
  defecto, y "the job's `permissions` block controlled API access but had no effect on cache
  writes" ([SafeDep](https://safedep.io/tanstack-github-actions-cache-poisoning/)). La página de GitHub dice ahora que un workflow así tiene acceso
  de solo lectura a la caché de la rama por defecto, salvo que declare un `cache-mode` que escriba,
  lo que "reintroduces the cache-poisoning risk this restriction is designed to prevent": la protección es un valor por defecto que un
  workflow puede desactivar.
- GitHub "provides a default event policy that blocks the `pull_request_target` event in public
  repositories", en evaluación ahora y aplicada desde el 2 de diciembre de 2026; y `actions/checkout`
  rechaza en ese evento la cabeza de una pull request de un fork salvo que se active
  `allow-unsafe-pr-checkout`.

Razonamiento, sin prueba: que el arnés de la base, con una pull request que no cambia ningún
workflow, deja ver al mantenedor antes de fusionar que el cambio no se juzgó a sí mismo. La prueba es la primera pull
request de A4 que cambie dokime y lleve su evidencia.

## Alternativas consideradas

- **Ejecutar el arnés de la propia pull request.** Es más sencillo, pero la autoauditoría pierde el
  sentido justo en las pull requests que cambian dokime.
- **`pull_request_target`, con el workflow de la base.** Cerraría el límite, pero el job ejecutaría el
  código del cambio con los secretos del repositorio, y con la caché de la rama por defecto, que los
  permisos del token no acotan y cuya protección un workflow puede desactivar; GitHub bloquea el
  evento por defecto en los repositorios públicos, y `actions/checkout` rechaza ahí el código de una
  pull request de un fork (ver la base).
- **Instalar una versión publicada de dokime.** No se publica nada hasta que alguien de fuera lo use
  (ADR-0068).

## Consecuencias

- Una pull request que cambia dokime se audita con el dokime de su base: sus comprobaciones nuevas
  solo valen desde la siguiente pull request tras su fusión, el coste que también declara
  microsoft-365-agents-toolkit: "Evaluation harness changes take effect after they are merged into
  the base branch".
- El workflow extrae dos veces: la base, para el arnés, y el proyecto con la pull request.
- En A4 la regla se cumple para el fichero del workflow por disciplina: antes de fusionar, el
  mantenedor comprueba que la pull request no cambia nada bajo `.github/workflows/`, y solo entonces
  lee el resumen del job como fiable.
