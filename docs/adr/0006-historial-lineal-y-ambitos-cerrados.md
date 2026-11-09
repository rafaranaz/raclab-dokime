# ADR-0006 · Historial lineal con rebase y ámbitos de commit cerrados

**Estado:** aceptada

## Contexto

Se quiere poder trabajar y revisar un módulo cada vez, y que el historial explique cada cambio.
Conventional Commits da formato a los mensajes, pero un ámbito libre (`fix(whatever): ...`) no
garantiza nada sobre qué toca el commit.

## Decisión

- Los ámbitos forman una lista cerrada en `tools/scopes.toml`, cada uno con las rutas que le
  pertenecen.
- Una rama declara un único ámbito en su nombre (`tipo/ámbito-descripción`). Sus commits deben usar
  ese ámbito y sus cambios deben quedar dentro de sus rutas, salvo las rutas compartidas: los ADR,
  la hoja de ruta y el propio `tools/scopes.toml`, para que una rama pueda declarar su ámbito.
- Los PR se integran por rebase: `main` tiene un historial lineal donde cada commit pasa las reglas.

## Alternativas descartadas

- **Squash merge.** Simplifica el historial, pero junta en un solo commit cambios que se hicieron
  y revisaron por separado, y el mensaje final no siempre conserva el porqué de cada paso.
- **Merge commits.** Mantienen las ramas, pero el historial deja de ser lineal y bisecable.

## Consecuencias

- Abrir un módulo nuevo empieza por declarar su ámbito y sus rutas, en la propia rama de ese
  módulo.
- Un cambio que necesita tocar dos ámbitos se parte en dos ramas. Es intencionado: es la señal de
  que el cambio no estaba bien delimitado.
- Como cualquier rama puede editar `tools/scopes.toml`, también podría ampliar sus propias rutas.
  La revisión del PR comprueba que una rama solo añade o cambia la entrada de su ámbito.
