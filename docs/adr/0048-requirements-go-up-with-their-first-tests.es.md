<!-- translation-of: 0048-requirements-go-up-with-their-first-tests.md sha256:b8966397763469aa -->
# ADR-0048 · Los requisitos se suben con sus primeros tests

**Estado:** propuesta

## Contexto

La skill [open-scope](../../.claude/skills/open-scope/SKILL.md) pedía abrir la pull request de un
ámbito como borrador con solo sus requisitos, antes de escribir código, para revisarlos antes de
construir sobre ellos. La puerta de trazabilidad falla cuando un requisito no tiene test, así que
ese borrador siempre está en rojo, y una pull request en rojo no se distingue de una rota. Los
ámbitos de `packs` (#28) y `core` (#40, #46) se construyeron de la otra manera: una sola pull
request, los requisitos en un commit y los tests y el código en el siguiente. El mantenedor lo pidió
así sin que antes se cambiara la skill.

## Decisión

Los requisitos de un ámbito se suben en la misma pull request que sus primeros tests, en commits
separados: primero los requisitos, después los tests y el código que los ponen en verde. No hay pull
request en borrador con la trazabilidad en rojo. El paso 4 de la skill open-scope lo dice.

## Base

Leído en la historia del repositorio: #28 tiene cuatro commits, el ámbito, los requisitos, la
comprobación y las reglas, y su documentación; #40 tiene el ámbito, los requisitos, el puerto y un enlace; #46
tiene los requisitos y los valores. Cada una se fusionó con todas las puertas en verde.
Razonamiento, sin prueba: que quien revisa lee primero los requisitos porque su commit va primero, y
que la revisión de los requisitos no pierde nada por llegar con un test que muestra qué significa
cada uno.

## Alternativas consideradas

- **Mantener el borrador con solo los requisitos.** Está en rojo por construcción, y cada ámbito
  empieza con una pull request que no se puede fusionar y una comprobación que no dice nada.
- **Eximir a los borradores de la puerta de trazabilidad.** Relaja una puerta, lo que necesita su
  propia ADR, para una pull request que nunca se fusiona tal como está.
- **Enseñar los requisitos al mantenedor fuera de una pull request**, en la conversación. Es lo que
  se hizo con `core` antes de #40, y no deja registro en el repositorio.

## Consecuencias

- La primera revisión de un ámbito llega con código. Si los requisitos están mal, los tests y el
  código del segundo commit se tiran con ellos.
- Un requisito que aún no tiene test no se puede subir, ni siquiera para discutirlo. Espera en la
  rama.
- Toda pull request de un ámbito está en verde cuando se abre, así que una en rojo siempre significa
  que algo está roto.
