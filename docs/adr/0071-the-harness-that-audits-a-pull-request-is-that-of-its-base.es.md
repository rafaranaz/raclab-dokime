<!-- translation-of: 0071-the-harness-that-audits-a-pull-request-is-that-of-its-base.md sha256:65e241d08f78468e -->
# ADR-0071 · El arnés que audita una pull request es el de su base

**Estado:** propuesta

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
  muestra, para que el mantenedor vea que es la base de la pull request.

**El límite.** El fichero del workflow sigue viniendo de la pull request, porque el evento es
`pull_request`: una pull request podría cambiarlo para que ejecute su propio dokime, o ninguno. Sin
`pull_request_target`, que la ADR-0070 rechazó, esto no tiene mecanismo; se cumple por disciplina,
porque las pull requests se abren con la cuenta del mantenedor, y el mantenedor comprueba en el
resumen que el commit del arnés es la base antes de fusionar.

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

Razonamiento, sin prueba: que el arnés de la base, nombrado por su commit en el resumen, deja ver al
mantenedor antes de fusionar que el cambio no se juzgó a sí mismo. La prueba es la primera pull
request de A4 que cambie dokime y lleve su evidencia.

## Alternativas consideradas

- **Ejecutar el arnés de la propia pull request.** Es más sencillo, pero la autoauditoría pierde el
  sentido justo en las pull requests que cambian dokime.
- **`pull_request_target`, con el workflow de la base.** Cerraría el límite, pero el job recibiría un
  token que puede escribir mientras ejecuta el código del cambio, lo que rechazó la ADR-0070.
- **Instalar una versión publicada de dokime.** No se publica nada hasta que alguien de fuera lo use
  (ADR-0068).

## Consecuencias

- Una pull request que cambia dokime se audita con el dokime de su base: sus comprobaciones nuevas
  solo valen desde la siguiente pull request tras su fusión, el coste que también declara
  microsoft-365-agents-toolkit: "Evaluation harness changes take effect after they are merged into
  the base branch".
- El workflow extrae dos veces: la base, para el arnés, y el proyecto con la pull request.
- En A4 la regla se cumple para el fichero del workflow por disciplina, y el resumen del job es lo
  que comprueba el mantenedor.
