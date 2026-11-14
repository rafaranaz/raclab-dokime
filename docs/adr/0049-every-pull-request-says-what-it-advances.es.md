<!-- translation-of: 0049-every-pull-request-says-what-it-advances.md sha256:5a56fe9464e23ded -->
# ADR-0049 · Toda pull request dice qué hace avanzar

**Estado:** propuesta

## Contexto

El 2026-11-14 el hito A2 tenía cinco ADR y ningún código que ejecutara `git` ni un contenedor. Su
criterio de salida es "The packs of the three repositories build and pass their self-check", y
buena parte del trabajo de esos días decidió detalles que no lo acercaban. Nada en una rama ni en una
pull request preguntaba para qué criterio o requisito era el trabajo.

## Decisión

Toda pull request empieza su descripción con una línea **Advances:** que nombra el criterio de
salida del hito abierto, o los requisitos, que hace avanzar. Si no hace avanzar ninguno, se pregunta
al mantenedor antes de escribirla. La plantilla de pull request tiene la línea, y la sección de pull
requests de [CONTRIBUTING.es.md](../../CONTRIBUTING.es.md) dice la regla.

## Base

Leído en las descripciones de las pull requests: de #39 a #49 todas han empezado con esa línea,
salvo #42, que abrió otra sesión y se cerró. Cuatro de ellas, #39, #45, #47 y #48, dicen que no
hacen avanzar ningún criterio de salida, o ninguno de forma directa, y el mantenedor había pedido
cada una. Razonamiento, sin prueba: que escribir la línea antes del trabajo deja ver una rama que no
sirve a ningún criterio cuando todavía es barato dejarla. La prueba que lo confirmaría es el resto
de A2: cuántas pull requests dicen que no hacen avanzar nada, y si se habían pedido.

## Alternativas consideradas

- **Dejarlo a la revisión.** La revisión ve el trabajo cuando ya está hecho, que es cuando más
  cuesta dejarlo.
- **Una comprobación de CI que rechace una descripción sin la línea.** Comprobaría que la línea
  existe, no que lo que dice es cierto. Se puede añadir si la línea empieza a olvidarse.
- **Enlazar cada pull request con una issue o un hito de GitHub.** Añade un segundo sitio que
  mantener al día, y los hitos y sus criterios ya viven en la hoja de ruta.

## Consecuencias

- Quien revisa lee primero para qué es la pull request, y puede parar ahí.
- El trabajo sobre el propio repositorio, como una regla de proceso, no hace avanzar ningún criterio
  de un hito. La línea lo dice, y el mantenedor la ha pedido.
- La regla depende de que la línea sea honesta. Nada lo comprueba salvo la revisión.
