<!-- translation-of: 0011-contract-of-requirements-and-approved-examples.md sha256:507606225947a727 -->
# ADR-0011 · Un contrato son requisitos EARS más ejemplos aprobados por una persona

**Estado:** propuesta

## Contexto

El contrato es aquello contra lo que se comprueba el resultado. Los requisitos en prosa dicen la
intención; tiene que decidir algo ejecutable. Con el mismo contenido, un formato estructurado no
cambia la corrección; la ambigüedad sí la daña.

## Decisión

- Un contrato contiene requisitos en EARS y ejemplos. **Los ejemplos deciden el veredicto**; los
  requisitos dicen la intención, dan a cada ejemplo algo a lo que referirse y permiten que la
  realimentación nombre un requisito sin revelar un ejemplo.
- Cada requisito declara su tipo: `new`, `change` o `preserve`. El tipo fija qué deben hacer sus
  ejemplos antes del cambio: fallar los de `new` y `change`, pasar los de `preserve`.
- Cada ejemplo lleva la etiqueta de su caso (normal, vacío, error…).
- Un contrato vive en un directorio por cambio, con el identificador de su historia, sus
  aclaraciones y su aprobación. Declara qué sustituye y qué tests existentes cambia. El contrato
  vigente de un repositorio es la unión de los contratos entregados.
- Las comprobaciones que no necesitan modelo van primero: sintaxis EARS, esquema de los ejemplos,
  requisito sin ejemplo, dos ejemplos con la misma entrada y distinto resultado, duplicados.

## Base

Literatura y razonamiento. El formato por sí solo no mejora la corrección
([estudio](https://arxiv.org/abs/2608.13742)); la ambigüedad semántica la baja
([estudio](https://arxiv.org/abs/2501.04810)). EARS se mantiene porque da enunciados atómicos cuya
sintaxis se puede comprobar. Que los ejemplos decidan es razonamiento.

## Alternativas consideradas

- **Solo requisitos.** Entonces un modelo tiene que convertir prosa en tests, y la puerta descansa
  en él.
- **Tests escritos en el marco de pruebas del proyecto como contrato.** Son código, una persona no
  los puede aprobar sin leer código, y corren dentro del proceso del sujeto.

## Consecuencias

- La persona aprueba más: varios ejemplos por requisito.
- Un requisito que no se pueda expresar como ejemplo solo se admite con una marca explícita, y la
  evidencia lo lista como no comprobado.
