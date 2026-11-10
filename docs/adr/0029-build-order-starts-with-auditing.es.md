<!-- translation-of: 0029-build-order-starts-with-auditing.md sha256:c8c067214bc0bddc -->
# ADR-0029 · El orden de construcción empieza por auditar un cambio que ya existe

**Estado:** propuesta

## Contexto

Lo que diferencia al producto es la verificación. Lanzar agentes es la parte más frágil y la menos
nuestra: depende de cada agente, de las políticas de los fabricantes y del aislamiento.

## Decisión

Siete bloques, cada uno con una orden que alguien puede usar, y dentro de cada uno un solo ámbito
de módulo abierto a la vez:

| Bloque | Qué se construye | Módulos, en orden |
|---|---|---|
| A · Auditar | Verificar un parche terminado contra un contrato escrito a mano | `core`, `contract`, `packs`, `sandbox` (entorno de verificación), `verify`, `evidence`, `interfaces` |
| B · Reservar | Ejemplos reservados y derivados | `oracle`, `verify`, `bench` |
| C · Lanzar | El arnés dirige a un agente, con el bucle y las impugnaciones | `sandbox` (trabajo), `agents`, `engine` |
| D · Proteger | Cobertura de líneas cambiadas, mapa de impacto, diferencias de comportamiento | `verify` |
| E · Atestar | Firmas, verificación independiente, repetición en CI | `evidence`, `delivery` |
| F · Especificar | Entrevista, propuestas de ejemplos, detectores, solucionador | `gateway`, `spec` |
| G · Generalizar | Un segundo lenguaje, más agentes, uso en equipo | `packs`, `agents`, `delivery` |

- El bloque C no se cierra hasta que el mismo cambio completa el circuito con dos perfiles de
  agente, uno de ellos con un modelo de pesos abiertos cercano a la frontera. Desde C, cada bloque
  termina con esa ejecución.
- El bloque A incluye ejecutar la auditoría en CI, que es el primer peldaño de la escalera de
  adopción ([ADR-0020](0020-agent-isolation-is-optional-adoption-is-a-ladder.es.md)). Su criterio
  de salida se mide sobre casos del conjunto ejecutados como tests normales; `bench` los
  automatiza en el bloque B.
- El bloque G existe porque "cualquier agente, cualquier lenguaje" es un objetivo declarado, y un
  objetivo sin bloque propio no se comprueba nunca.
- Primer lenguaje: Python; Java llega en el bloque G. Quedan fuera de la primera versión la interfaz gráfica, varios
  repositorios por proyecto y un índice de código con precisión de compilador.

## Base

Razonamiento. El bloque A es el corte más pequeño que ejercita lo propio, no depende de ningún
agente y se puede usar sobre las peticiones de integración de este repositorio desde el primer
día.

## Alternativas consideradas

- **Lanzar un agente primero.** Recorre todo el circuito pronto, pero construye el bucle sobre una
  verificación que nadie ha medido.
- **La especificación primero.** Es lo más difícil para el usuario, pero todo lo posterior depende
  de que la verificación funcione.

## Consecuencias

- El bucle de reintentos, donde aparecen el coste y la fuga por realimentación, llega en el tercer
  bloque. Los bloques B y C se pueden intercambiar si hay que verlo antes.
- El alcance es grande para una persona; cada bloque tiene que valer por sí mismo.
