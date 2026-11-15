<!-- translation-of: 0054-the-policy-is-an-optional-file-of-values.md sha256:a9ab3c616a385fdf -->
# ADR-0054 · La política es un fichero opcional de valores, y la primera versión tiene dos

**Estado:** aceptada

## Contexto

Varias decisiones aceptadas dejan un valor a la política, y la evidencia registra la política por
su huella ([ADR-0023](0023-evidence-is-an-attestation-bound-to-the-tree.es.md)). Ninguna decisión dice
todavía qué es ese fichero. Leído en las ADR, por el bloque que necesita cada valor:

| Valor | Dónde | Bloque |
|---|---|---|
| Cuántas veces se ejecuta la línea base, "dos para empezar" | ADR-0017 | A |
| Cuántas veces se ejecuta la verificación, para el gate `repeatability` | `docs/architecture/04-states-and-flows.md` | A |
| Qué gates se pueden omitir | ADR-0015 | D (el único ejemplo es la cobertura) |
| El umbral de cobertura de las líneas cambiadas | ADR-0017 | D |
| Los presupuestos de los bucles del flujo | ADR-0018 | C |
| El envoltorio del agente | ADR-0020 | C |
| La consistencia formal; el ejemplo plantado | ADR-0026; arquitectura | F |

## Decisión

- **El fichero es `.dokime/policy.yaml`, y es opcional.** Sin él se aplican los valores por defecto
  que define `core`.
- **La primera versión tiene dos valores**:

  ```yaml
  format: 1
  baseline:
    runs: 2
  verification:
    runs: 2
  ```

  Los dos son números enteros de al menos 2: con una sola ejecución no se puede ver un test inestable
  ni un veredicto que varía.
- **Lo lee el lector estricto** de la [ADR-0037](0037-a-contract-is-read-by-strict-rules-of-its-own.es.md),
  con campos cerrados: un campo desconocido es un hallazgo, no un valor por defecto en silencio.
- **La evidencia registra la política efectiva**, la leída del fichero o la de los valores por
  defecto, por la huella de su forma normalizada, y dice cuál de las dos fue. Así el veredicto se
  puede recalcular (INV-4).
- **Cada bloque posterior añade el campo que necesita, con un valor por defecto**, para que una
  política escrita antes siga siendo válida. Mientras solo se añadan campos, el formato sigue siendo
  1.
- **Los límites de una construcción, de una ejecución y de la lectura de un informe no están en
  ella.** Siguen siendo los valores por defecto de `core` que pasa quien llama
  ([ADR-0045](0045-a-test-report-is-read-by-a-bounded-reader-that-refuses-any-dtd.es.md)); entran en
  la política cuando un proyecto necesite otros valores.

## Base

Leído: las ADR de la tabla de arriba. Codecov guarda su configuración en un fichero opcional del
repositorio sobre valores por defecto ([Codecov](https://docs.codecov.com/docs/codecov-yaml)), y un
proyecto construyó una acción porque Codecov no avisa cuando ese fichero está roto
([action-check-codecov-config](https://github.com/formsort/action-check-codecov-config)); el lector
estricto responde a eso. Un lenguaje de reglas como Rego se elige cuando la lógica de una política
es compleja ([comparación](https://www.techplained.com/kyverno-vs-opa-gatekeeper)); esta política
son dos números. Razonamiento, sin test: que un fichero opcional baja el primer paso de la adopción,
y que registrar la política efectiva mantiene completa la evidencia sin él.

## Alternativas consideradas

- **Un fichero obligatorio.** Un fichero más que escribir antes de una primera auditoría, para dos
  números que tienen valor por defecto.
- **Un lenguaje de reglas.** No hay reglas que escribir.
- **Todos los campos ya**, para los bloques C, D y F. Se decidirían antes que los bloques que los
  probarían.
- **Los valores como opciones de la orden.** No están protegidos, y es fácil cambiarlos en una
  ejecución sin dejar rastro en el repositorio.

## Consecuencias

- A3 lee la política, o sus valores por defecto, y la registra en la evidencia.
- Un campo que añade un bloque posterior llega con su valor por defecto y su requisito.
- La política ya es una ruta protegida
  ([`03-data-and-evidence.es.md`](../architecture/03-data-and-evidence.es.md)); ahí no cambia nada.
