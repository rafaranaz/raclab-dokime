<!-- translation-of: 0050-an-experiment-enters-the-repository-as-a-test.md sha256:00c0e5f3d2973c27 -->
# ADR-0050 · Un experimento entra en el repositorio como un test

**Estado:** propuesta

## Contexto

Las ADR de A2 se apoyan en medidas hechas fuera del repositorio. La ADR-0043 cita el programa que
carga un contenedor; la ADR-0044 dice que su regla de orden se escribió en 25 líneas de Python y se
comparó con `git rev-list` en seis repositorios; la ADR-0045 describe un lector de informes, la
apertura de una ruta sin enlaces y un lector en un proceso propio. Ninguno de esos programas, ni
ninguno de los repositorios hechos para las pruebas, está en el repositorio. Ningún workflow ejecuta
`docker` ni `podman`, así que CI no comprueba las cuatro garantías de la ADR-0043.

## Decisión

Una medida en la que se apoya una decisión entra en el repositorio como un test o un fixture del
ámbito al que pertenece, cuando ese ámbito se abre, con su requisito. La base de la ADR da el
resultado y nombra el test, o dice que todavía está por venir y en qué ámbito. Un programa no se
guarda como prosa en la base. La skill adr lo dice en su sección sobre la base.

## Base

Leído en el repositorio el 2026-11-14: una ADR cita un programa, dos describen programas que no
están en el repositorio y ningún workflow usa un motor. Razonamiento, sin prueba: que una medida
guardada como prosa no se vuelve a ejecutar cuando cambian el código o el motor, y un test sí. La
prueba que lo confirmaría está en los ámbitos de A2: la regla de orden en `packs`, el lector en
`sandbox` y las garantías de la ADR-0043 en la CI de `sandbox`, cada una comprobada de nuevo en cada
pull request.

## Alternativas consideradas

- **Mantener los programas en la base**, como hace la ADR-0043. Se leen, no se ejecutan, y nada dice
  cuándo dejan de ser ciertos.
- **Un directorio de experimentos fuera de los ámbitos.** Tendría código que ninguna puerta ejecuta
  y que ningún requisito pide.
- **Enlazar el programa en otro sitio**, como un gist o el directorio de trabajo de una sesión. Sale
  del repositorio, y el enlace se puede romper.

## Consecuencias

- Las ADR-0043, 0044 y 0045 están aceptadas y no se reescriben. Sus programas entran como tests
  cuando se abran `sandbox` y `packs`: el programa de carga, la regla de orden con sus repositorios,
  el lector con sus informes hostiles.
- Un test de un motor necesita el motor en CI. Uno que se salta porque no hay motor tiene que fallar,
  no pasar en silencio; eso es un requisito de `sandbox`.
- Una ADR puede decir ahora que su medida está por venir. Eso solo es honesto si nombra el ámbito
  que la va a tener.
