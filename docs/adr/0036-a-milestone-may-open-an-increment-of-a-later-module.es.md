<!-- translation-of: 0036-a-milestone-may-open-an-increment-of-a-later-module.md sha256:b6e82f2e4a32ed90 -->
# ADR-0036 · Un hito puede abrir un incremento de un módulo posterior

**Estado:** aceptada

## Contexto

El [ADR-0029](0029-build-order-starts-with-auditing.es.md) lista los módulos de cada bloque en
orden, con un solo ámbito de módulo abierto a la vez. En el bloque A, `interfaces`, donde viven
las órdenes, es el último. El primer hito con código, A1, entrega una orden que valida un
contrato, y su lógica solo necesita `core` y `contract`. Seguido al pie de la letra, el orden deja
A1 sin nada que una persona pueda ejecutar hasta que el bloque entero esté construido.

## Decisión

- El orden del ADR-0029 es el orden en que se abren los módulos de un bloque para su trabajo
  principal.
- Un hito puede abrir, antes de ese orden, un incremento de un módulo posterior cuando lo que el
  hito entrega no se puede enseñar sin él. El incremento contiene solo lo que esa entrega
  necesita.
- Sigue habiendo un solo ámbito de módulo abierto a la vez, y la hoja de ruta nombra el incremento
  en la fila del hito.
- A1 abre `interfaces` solo para la orden `contract check`. A3 lo vuelve a abrir para `audit`.

## Base

Razonamiento. El ADR-0029 eligió el orden para que cada bloque entregue una orden que alguien
pueda usar; un incremento abierto antes sirve a ese mismo fin dentro de un bloque. No se ha
buscado ninguna fuente externa: es un punto de coherencia interna entre el plan y la tabla de
módulos.

## Alternativas consideradas

- **Mantener el orden y entregar A1 como biblioteca.** La validación queda probada, pero nadie
  puede ejecutarla hasta A3, y los contratos escritos a mano del corpus solo los comprueba código
  de test.
- **Poner la orden en `contract`.** Rompe la regla de que `interfaces` es el único sitio con
  órdenes y la raíz de composición ([ADR-0031](0031-modules-depend-only-on-core.es.md)).

## Consecuencias

- `interfaces` existe desde A1, con una orden y sin lógica de dominio.
- Un módulo puede tener varios incrementos dentro de un bloque; cada uno es un ámbito que se abre
  y se cierra con sus propios requisitos.
