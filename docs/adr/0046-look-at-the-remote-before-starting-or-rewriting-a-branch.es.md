<!-- translation-of: 0046-look-at-the-remote-before-starting-or-rewriting-a-branch.md sha256:1f6b065e1262b330 -->
# ADR-0046 · Mirar el remoto antes de empezar o reescribir una rama

**Estado:** propuesta

## Contexto

Más de una sesión, del mantenedor o de un agente, trabaja a la vez en este repositorio, y ninguna ve
lo que otra no ha subido. El 2026-11-13 y el 2026-11-14 eso costó cuatro veces:

- La aceptación de la ADR-0042 se preparó en dos ramas, `docs/arch-accept-repository-port` (#32,
  fusionada) y `docs/arch-accept-adr-0042`, borrada sin pull request.
- La aceptación de la ADR-0043 la abrió una sesión como #35 y la empezó otra, que el mantenedor
  paró antes de su commit.
- `docs/arch-run-engines` (#34), ya subida, la rebasó y corrigió una sesión mientras otra preparaba
  su propio rebase de la misma rama para subirlo con `--force-with-lease`.
- La aceptación de la ADR-0044 se abrió dos veces, #41 y #42, con dieciséis segundos de diferencia.
  #42 se cerró.

## Decisión

Antes de empezar una rama, antes de reescribir una que ya está en el remoto y antes de un commit que
cambia el estado de una ADR, se listan las ramas y las pull requests abiertas del remoto
(`git fetch --prune`, `git branch -r`, `gh pr list`). Si alguna ya hace el mismo trabajo, no se
empieza la nueva, o se empieza a partir de ella. La regla está escrita en la sección de ramas de
[CONTRIBUTING.es.md](../../CONTRIBUTING.es.md) y en las reglas de trabajo de
[CLAUDE.md](../../CLAUDE.md), que carga cada sesión.

## Base

Los cuatro casos de arriba, leídos en la lista de pull requests del repositorio y en el reflog de
una de las sesiones:

- En el primero, #32 llevaba seis minutos abierta cuando se empezó la segunda rama.
- En el segundo, #35 estaba abierta cuando empezó la otra sesión.
- En el tercero no consta qué push llegó antes.
- En el cuarto, la sesión de #41 había listado el remoto justo antes de abrirla, y #42 llegó
  dieciséis segundos después.

Un listado habría mostrado los dos primeros. No puede mostrar trabajo que aún no se ha subido.

Razonamiento, sin prueba: que el listado quita la mayoría de los duplicados al coste de dos órdenes.
La prueba que lo confirmaría es contar las ramas y pull requests duplicadas durante el resto del
bloque A, con la regla en vigor.

## Alternativas consideradas

- **Sin regla; la revisión cierra los duplicados.** Es lo que pasó en los cuatro casos. Cada uno
  costó una rama, una pull request o un rebase que alguien tuvo que ver y tirar.
- **Una sola sesión a la vez.** Quita el problema y el trabajo en paralelo que quiere el mantenedor.
- **Una comprobación de CI que rechace una pull request que cambia el estado de una ADR que otra
  pull request abierta también cambia.** Solo actúa cuando las dos están abiertas, con el trabajo
  ya hecho. Se puede añadir más adelante si siguen los duplicados.
- **Reservar el trabajo antes**, con una issue o una pull request en borrador vacía, antes de
  escribir nada. Añade un paso a cada rama, y dos reservas hechas con segundos de diferencia chocan
  igual que #41 y #42.
- **Confiar en `--force-with-lease`.** Rechaza un push que descartaría commits que otro subió, y
  solo eso: no hace nada contra dos ramas que hacen el mismo trabajo.

## Consecuencias

- Cada rama, cada reescritura de una rama subida y cada cambio de estado empieza con dos órdenes.
  Sin `gh`, las pull requests se miran en la web.
- Dos sesiones que empiezan el mismo trabajo con segundos de diferencia siguen chocando, como #41 y
  #42. La regla lo hace raro; no lo impide.
- Una reescritura sigue usando `--force-with-lease`, que cubre lo que un listado no puede: los
  commits subidos entre el listado y el push.
