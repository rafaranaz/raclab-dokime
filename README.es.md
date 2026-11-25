<!-- translation-of: README.md sha256:b072d4662d75a65f -->
# raclab-dokime

*Read in [English](README.md).*

Una capa de verificación y evidencia alrededor de los agentes de programación. No escribe código:
ayuda a una persona a escribir un contrato de requisitos y ejemplos aprobados, entrega el trabajo a
un agente que el usuario ya tiene, y acepta el resultado solo a través de puertas mecánicas. Lo que
entrega es un cambio con evidencia firmada de qué se comprobó, qué no, y quién decidió qué. Ningún
resultado se da por bueno por la palabra del agente que lo produjo.

## Estado

En construcción, en la versión **0.2.0**. La arquitectura de referencia está escrita y sus
decisiones están aceptadas. De los siete bloques de construcción de la fase 2 hay dos cerrados:
**A** (auditar) y **B** (reservar). El bloque C, en el que el arnés lanza al agente, no se ha
abierto. Las fases, los bloques y sus criterios de salida están en
[docs/ROADMAP.es.md](docs/ROADMAP.es.md).

Verifica solo proyectos de Python, los observa en contenedores solo con podman, y llega al código
por dos fronteras: una función llamada con valores JSON y una línea de órdenes.

### Las órdenes que existen

| Orden | Qué hace | Qué comprueba |
|---|---|---|
| `dokime contract check` | Valida un fichero de contrato y dice qué le falta | El formato, el texto EARS de cada requisito, un ejemplo para cada requisito, duplicados y contradicciones. No ejecuta nada |
| `dokime contract seal` | Reparte un contrato aprobado y sella sus ejemplos reservados para los destinatarios de `.dokime/recipients.txt` | Que el contrato escrito deja visibles exactamente los ejemplos del reparto, y que ningún ejemplo reservado se escribe en el proyecto |
| `dokime env check` | Autocomprueba el pack de un proyecto sobre su historia | Que la imagen del pack se construye, y que dos commits de la historia tienen tests que pasan de rojo a verde en ella |
| `dokime audit` | Audita un cambio que llega ya hecho, un parche sobre un commit base, contra su contrato, y escribe el registro de la ejecución y un fichero de evidencia | Las puertas `contract`, `environment`, `baseline`, `protected-paths`, `existing-tests`, `visible-examples`, `repeatability`, `relations`, y `sealed-examples` donde está la clave |

Cada orden escribe una línea por hallazgo y sale con un código para cada veredicto. Cómo se usa
cada una está en el README de [`interfaces`](src/dokime/interfaces/README.md).

### Qué ha medido

Sobre un corpus de casos en tres proyectos públicos, con veredictos conocidos: ninguna aceptación
falsa con parches que fallan ejemplos visibles, editan tests o rompen tests existentes (bloque A),
ni con las cuatro técnicas de trampa de la hoja de ruta (bloque B). Los casos malos los escribió la
sesión que construye, no un agente que intenta hacer trampa. Los números y sus límites están en las
notas de cierre del [bloque A](docs/ROADMAP.es.md#bloque-a--nota-de-cierre) y del
[bloque B](docs/ROADMAP.es.md#bloque-b--nota-de-cierre).

### Qué no hace todavía

- **No lanza un agente.** El cambio llega ya hecho, lo escriba quien lo escriba; el bucle que
  entrega la tarea a un agente llega con el bloque C.
- **No mira el daño fuera del cambio.** Las puertas `changed-line-coverage` y
  `behaviour-differences` aparecen en la evidencia como no aplicables, se construyen en el bloque D.
- **La evidencia no está firmada.** Es una declaración sin firmar; firmarla, y verificarla sin el
  arnés, llegan con el bloque E.
- **No ayuda a escribir el contrato.** Lo escribe una persona a mano; la ayuda llega con el
  bloque F.
- **La puerta de los ejemplos sellados no se ejecuta en CI**
  ([ADR-0082](docs/adr/0082-the-sealed-gate-does-not-run-in-ci-in-block-b.es.md)): se ejecuta solo
  donde está la clave, a mano.
- **De las relaciones, solo `idempotent` en la línea de órdenes** se ha medido, en un caso.

## Dónde está cada cosa

| Qué | Dónde |
|---|---|
| Cómo se trabaja: ramas, commits, puertas, definición de terminado | [CONTRIBUTING.es.md](CONTRIBUTING.es.md) |
| Qué es el producto, sus invariantes y sus módulos | [docs/architecture/](docs/architecture/README.es.md) |
| Decisiones de diseño y de proceso | [docs/adr/](docs/adr/README.es.md) |
| Requisitos EARS de cada ámbito | [docs/requirements/](docs/requirements/) |
| Fases y criterios de salida | [docs/ROADMAP.es.md](docs/ROADMAP.es.md) |

## Desarrollo

Requiere [uv](https://docs.astral.sh/uv/).

```bash
uv sync --locked
uv run pytest
```

Las puertas que ejecuta CI están en [CONTRIBUTING.es.md](CONTRIBUTING.es.md#puertas-de-calidad).
