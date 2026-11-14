<!-- translation-of: 0051-the-adapters-that-run-a-program-are-exempt-from-s603.md sha256:ef9ef8356560ffe9 -->
# ADR-0051 · Los adaptadores que ejecutan un programa quedan fuera de S603

**Estado:** propuesta

## Contexto

El adaptador del repositorio del proyecto ejecuta `git`, y el adaptador del entorno de verificación
ejecutará `podman` ([ADR-0042](0042-a-port-of-the-project-repository-composes-the-trees-that-are-built.es.md),
[ADR-0043](0043-tests-run-only-on-an-engine-that-enforces-the-limits.es.md)). Ejecutar un programa
es para lo que existen. La puerta de lint selecciona las reglas `S` de ruff, y S603 avisa de toda
llamada que arranca un proceso sin shell cuando sus argumentos no son literales. La primera versión
del adaptador de git tiene dos llamadas así, y las dos dan aviso. `tests/**` y `tools/**` ya están
fuera de S603 y S607; `src/` no.

## Decisión

La regla S603 no se aplica a `src/dokime/platform/**` ni a `src/dokime/sandbox/**`, con una
exclusión por fichero en `pyproject.toml`. Todas las demás reglas `S` siguen en vigor ahí, S602
(una llamada con shell) y S607 (un programa nombrado con una ruta parcial) incluidas: un adaptador
resuelve la ruta de su programa una vez al abrirse, con `shutil.which`, y ejecuta siempre esa ruta,
para que la evidencia pueda registrar qué programa y qué versión se usaron.

## Base

Leído en la documentación de ruff: S603 comprueba "method calls that initiate a subprocess without a
shell", y es "prone to false positives" porque no puede saber si los argumentos se validaron; S607
avisa de "the starting of a process with a partial executable path", porque un cambio de `PATH`
podría ejecutar otro programa. Medido en el adaptador de git: S603 avisó de sus dos llamadas a
`subprocess.run`, cada una con una lista de argumentos que construye el adaptador y sin shell. No
buscado: cómo acotan esta regla otros proyectos. Razonamiento, sin prueba: que una exclusión acotada
a los dos módulos cuyo trabajo es ejecutar un programa dice lo mismo que una marca en cada llamada,
en un solo sitio, y deja la regla en vigor donde una llamada a un programa sería una sorpresa.

## Alternativas consideradas

- **Un `# noqa: S603` en cada llamada.** Relaja la misma regla, repartida por las llamadas, sin
  ninguna decisión escrita; una llamada nueva en otro módulo se silenciaría igual.
- **Excluir todo `src/`.** Una llamada a un programa en un módulo de dominio, que no debe hablar
  con el exterior, dejaría de dar aviso.
- **Excluir también S607 y ejecutar `git` por su nombre.** El programa que se ejecuta dependería
  del `PATH` de cada llamada, y la evidencia no podría decir cuál fue.

## Consecuencias

- Los dos módulos de adaptadores pueden arrancar procesos con argumentos que calculan; la revisión,
  no la puerta, comprueba que esos argumentos vienen del adaptador y no del proyecto.
- La puerta sigue rechazando en los adaptadores un programa nombrado con una ruta parcial, o una
  llamada a través de una shell.
- Otro módulo que necesite ejecutar un programa necesita otra ADR.
