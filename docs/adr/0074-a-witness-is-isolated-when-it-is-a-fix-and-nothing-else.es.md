<!-- translation-of: 0074-a-witness-is-isolated-when-it-is-a-fix-and-nothing-else.md sha256:44c13f5d3b1b8694 -->
# ADR-0074 · Un testigo está aislado cuando es un arreglo y nada más

**Estado:** aceptada

## Contexto

La [ADR-0057](0057-the-cases-of-the-corpus-come-from-witnesses-that-fit-a-boundary.es.md) solo
acepta un testigo como parche bueno si está *aislado*, que su cambio de código sea el arreglo, no
una refactorización ni un cambio de las herramientas de los tests, y es *expresable* en una frontera
del contrato. No dice si una funcionalidad nueva, una deprecación o una publicación son un arreglo.

La medida que cerró el bloque A leyó dos veces los 41 testigos del corpus, sin que ninguna lectura
viera la otra. Coincidieron en 36 de 41 en expresable (κ 0,75) y solo en 33 en aislado (κ 0,57), y
las ocho diferencias en aislado fueron en el mismo sentido: la primera lectura tomó aislado como "el
cambio es un arreglo", la segunda como "el cambio es solo el comportamiento buscado, sin
refactorización ni herramientas", lo que deja entrar una funcionalidad.

Un conjunto de errores reales como Defects4J parte de commits que el gestor de incidencias del
proyecto ya enlaza con un error. Los testigos del corpus no llevan esa etiqueta: un testigo es un
commit que toca los tests y pone algunos en verde, sea lo que sea.

La revisión estratégica al cerrar el bloque A recomendó la definición de Defects4J; el mantenedor la
aprobó y pidió que esta ADR diga cómo se decide que un testigo es un arreglo. La sesión que revisa
el trabajo encontró el hueco en la medida; la decisión es del mantenedor.

## Decisión

Esta ADR enmienda la ADR-0057 en su filtro *aislado*; el resto sigue en pie.

**La regla.** Un testigo está aislado cuando su cambio fuera de los tests es el arreglo de un
comportamiento y nada más: no una funcionalidad, una refactorización, una deprecación, la retirada de
algo admitido, una publicación ni un cambio de herramientas.

**Cómo se decide que un testigo es un arreglo, leyendo, en el corpus.** Cuatro condiciones, cada una
leída en el commit y en su base; un testigo está aislado cuando cumple las cuatro, y su etiqueta
nombra la primera que no cumple:

1. **La interfaz existe en la base.** Los tests que pone en verde solo usan nombres, parámetros,
   opciones y formatos de fichero que la base ya tiene. Un test que falla en la base porque falta
   uno de ellos quiere decir que el testigo añade una funcionalidad.
2. **La base se equivoca.** En la base, lo que comprueban esos tests está mal de una de tres formas:
   - contradice lo que el proyecto ya decía: su documentación, sus docstrings o tipos, una
     incidencia que cite el commit, u otro comportamiento de la misma interfaz;
   - es un error que el proyecto no controla, una excepción inesperada o un cuelgue, ante una
     entrada válida;
   - incumple una especificación externa que el proyecto declara seguir, como SemVer 2.0 en
     python-semver o CommonMark en mdformat.

   Si no se da ninguna y la base documentaba el comportamiento anterior como buscado, o como no
   especificado, el testigo cambia un comportamiento; no lo arregla.
3. **No se quita nada.** El cambio no retira ningún comportamiento admitido, no añade una deprecación
   y no es solo un cambio de la versión o del empaquetado.
4. **No viene nada más.** El diff fuera de los tests solo contiene el arreglo; un arreglo que viene
   con una funcionalidad, una refactorización o herramientas está enredado, y no aislado.

El mensaje del commit, o una etiqueta "fix" en su pull request, apoya la lectura pero no la decide.

**La medida da dos proporciones**, como hizo el cierre del bloque A: los testigos que caben,
aislados y expresables, que es la proporción de arreglos reales que pide la ADR-0057; y los testigos
expresables sean lo que sean, porque la hipótesis de A0 habla de requisitos y una funcionalidad
también es un requisito.

## Base

Comprobado en [Defects4J](https://homes.cs.washington.edu/~rjust/publ/defects4j_issta_2014.pdf)
(Just, Jalali y Ernst, ISSTA 2014) y en su [README](https://github.com/rjust/defects4j):

- Entre los requisitos de cada error, en la sección 2: "The bug fix (i.e., the diff between Vbug and Vfix) does not include unrelated changes such as
  features or refactorings."
- Sus candidatos salen del enlace entre un commit y el gestor de incidencias: "the commit log
  references a bug id of the bug tracking system or 2) the bug tracking system references a commit
  id of the version control system."
- Esa etiqueta no basta: "we encountered several types of fixes not related to the source code, or
  features, which were classified as a 'bug fix' by developers."
- Aislar se hace leyendo: "We manually reviewed the source code diffs of reproducible bugs to verify
  that they did not include irrelevant changes."; y su README dice que cada error está "Minimized:
  the Defects4J maintainers manually pruned out irrelevant changes in the commit (e.g., refactorings
  or feature additions)."

Medido al cerrar el bloque A (`tests/corpus/witnesses.toml`): el acuerdo de las dos lecturas, 33,
36 y 38 de 41 en aislado, expresable y ambos (κ 0,57, 0,75 y 0,84).

Razonamiento, sin prueba: que las cuatro condiciones hacen que dos lecturas coincidan en aislado
más que con κ 0,57. La prueba, antes de que el bloque B amplíe el corpus: los ocho testigos en que
las dos lecturas difirieron en aislado se vuelven a etiquetar solo con estas cuatro condiciones, por
dos lectores que no se ven entre sí. Uno es un agente nuevo, que no ha visto las etiquetas
anteriores ni el debate sobre ellas, como se hizo la primera lectura; el otro es la sesión que revisa
el trabajo, cuya nota dice que conocía el debate. Se recalcula κ sobre los ocho.

## Alternativas consideradas

- **La segunda lectura, "solo el comportamiento buscado".** Más amplia, y deja que una funcionalidad
  sea un parche bueno, que no es lo que cuenta la proporción de arreglos reales de la ADR-0057 y se
  aparta de la referencia publicada.
- **La etiqueta del proyecto**: tomar como arreglo el testigo cuyo commit, o la incidencia que cita,
  está etiquetado como error en su gestor. Muchos testigos no citan ninguna incidencia, leer el
  gestor necesita la red en cada medida, y Defects4J encontró funcionalidades con esa etiqueta; en
  lugar de decidir, apoya la lectura.
- **Minimizar el parche a mano, como hace Defects4J**, quitando del commit los cambios que no son el
  arreglo. El parche bueno de un caso es el commit tal cual, todo lo que queda fuera de los tests
  (ADR-0057), y editarlo devolvería la elección a mano que quita tomar los casos de los testigos.
- **Quitar el filtro.** La medida dejaría de distinguir arreglos de funcionalidades, y un parche
  enredado confundiría lo que detecta cada puerta de un caso.

## Consecuencias

- Las etiquetas de una medida nombran la primera condición que un testigo no cumple, para que dos
  lecturas se puedan comparar condición a condición.
- Los casos que el bloque B añada al corpus toman sus parches buenos de testigos aislados según esta
  definición.
- Las etiquetas del cierre del bloque A se quedan como se leyeron; la prueba de arriba solo vuelve a
  etiquetar las ocho en disputa.
- Leer un testigo lleva más tiempo: la segunda condición pide la documentación de la base, no solo
  el diff.
