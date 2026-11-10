<!-- translation-of: 0028-language-support-is-a-declarative-pack-with-levels.md sha256:2d1b4543fd7ac1c9 -->
# ADR-0028 · El soporte de un lenguaje es un pack declarativo con niveles

**Estado:** propuesta

## Contexto

El núcleo no debe saber de lenguajes. Montar automáticamente el entorno de un repositorio
cualquiera funciona entre el 17 % y el 38 % de las veces, y el 12,7 % de los resultados pasan sin
probar nada de verdad.

## Decisión

- Un pack son datos: cómo reconocer el proyecto, su entorno, las órdenes de construir, probar y
  medir cobertura, cómo servirlo, su sonda, sus rutas protegidas y sus servicios acompañantes.
- El entorno sale de lo que el proyecto ya tiene: un Dockerfile, un devcontainer o su
  configuración de CI. Un pack propuesto a partir de ellos se verifica antes de aceptarse.
- Tres niveles, registrados en la evidencia:

  | Nivel | Requiere | Habilita |
  |---|---|---|
  | P1 | Entorno, construcción, tests con un informe estándar | Auditoría de regresión |
  | P2 | Un ejecutable o un servicio | Ejemplos en las fronteras `cli` y `http` |
  | P3 | Una sonda y cobertura | La frontera `function`, cobertura de líneas cambiadas, mapa de impacto |

- El pack se comprueba a sí mismo con la historia del proyecto: un commit que añadió un test junto
  a un arreglo debe tener ese test fallando en el commit padre y pasando en el del arreglo.

## Base

Literatura y una prueba propia parcial.
[Multi-Docker-Eval](https://arxiv.org/abs/2512.06915) para la dificultad. Nuestra prueba tomó las
órdenes de la CI de diez repositorios públicos: funcionaron cinco de los seis que se pudieron
medir; hay que repetirla con contenedores y acceso a los registros antes de que cuente.

## Alternativas consideradas

- **Código de lenguaje repartido por varios módulos.** Cada lenguaje nuevo tocaría el núcleo.
- **Comprobar el pack rompiendo un fichero fuente.** Falla antes el linter o el compilador, lo que
  no demuestra que los tests ejerciten el código.

## Consecuencias

- P1 y P2 no necesitan nada escrito por lenguaje, lo que hace creíble "cualquier lenguaje" pronto.
- Un proyecto sin un commit de esa forma tiene un pack sin autocomprobación, y se anota.
