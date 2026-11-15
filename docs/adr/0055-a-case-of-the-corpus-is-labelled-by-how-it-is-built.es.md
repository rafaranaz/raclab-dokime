<!-- translation-of: 0055-a-case-of-the-corpus-is-labelled-by-how-it-is-built.md sha256:ed9f1a281c830516 -->
# ADR-0055 · Un caso del conjunto de casos se etiqueta por cómo se construye, y se confirma antes de ejecutarse

**Estado:** aceptada

## Contexto

El arnés se mide sobre un conjunto de casos con veredictos conocidos
([ADR-0030](0030-the-harness-is-measured-on-a-corpus-with-known-verdicts.es.md)). El criterio de
salida del hito A3 se mide sobre los diez primeros casos del conjunto, etiquetados antes de
ejecutarlos. Las mismas personas que construyen el arnés escriben los casos, así que un caso se
puede inclinar, sin que nadie lo pretenda, hacia lo que el arnés ya hace. Una etiqueta decidida
después de ver lo que dijo el arnés no mide nada.

## Decisión

- **Qué es un caso.** Un proyecto en un commit base, nombrado por su repositorio y su commit
  completo como en `tests/corpus/<project>/source.toml`; un contrato de requisitos EARS y ejemplos
  ([ADR-0011](0011-contract-of-requirements-and-approved-examples.es.md)); un parche; y el veredicto
  esperado con su etiqueta de la ADR-0030.
- **Dónde vive un caso.** En `tests/corpus/<project>/cases/<case>/`, junto al pack de su proyecto.
  CORPUS-001, que hoy solo admite el pack, el Dockerfile y la fuente en el directorio de un
  proyecto, cambia con él cuando se abra el ámbito `corpus` en A3.
- **De dónde salen los parches buenos.** De commits de los proyectos del conjunto que arreglaron
  código junto con su test, cuyo test pasa de rojo a verde. Los testigos que encuentra la
  autocomprobación de un pack
  ([ADR-0044](0044-the-packs-module-drives-the-self-check-in-an-order-of-its-own.es.md)) son esos
  commits. La base es el padre; el parche es el cambio del código que no es test. La
  autocomprobación para en el segundo testigo y no los guarda, así que da dos por proyecto, seis en
  total; con los parches que se derivan de ellos basta para los diez casos de A3. Buscar testigos
  más allá del segundo hará falta cuando el conjunto crezca hacia los treinta casos de la
  [ADR-0030](0030-the-harness-is-measured-on-a-corpus-with-known-verdicts.es.md), en el bloque B, y
  no se construye antes.
- **Los parches malos se derivan de uno bueno**, uno por cada etiqueta que nombra el criterio de
  salida de A3:
  - *falla un ejemplo visible*: un arreglo parcial;
  - *edita tests*: se cambia o se quita el test que fallaba en lugar del código;
  - *rompe tests existentes*: el arreglo junto con una regresión en otro sitio.

  La etiqueta sale de cómo se construyó el parche, no de lo que el arnés diga de él.
- **Quién escribe y quién confirma.** El contrato y los parches derivados los redacta una sesión de
  asistente; el mantenedor aprueba el contrato y confirma la etiqueta.
- **Antes de que un caso se ejecute por primera vez**, se fusiona en `main` con su etiqueta, y el
  mantenedor ha leído su contrato, su parche y su etiqueta y ha confirmado el veredicto que esperan.
  Si el mantenedor no está de acuerdo, el caso se corrige o se descarta antes de ejecutarse. Se
  registran los minutos que el mantenedor dedica a cada caso, como una de las métricas de la
  ADR-0030.
- **Una etiqueta no cambia nunca después de que el caso se ejecutó.** Una corrección es un caso
  nuevo con su motivo; el antiguo se conserva y se marca como retirado.
- **Una puerta** comprueba que cada caso tiene etiqueta y que los ficheros de un caso no han
  cambiado desde el commit que lo añadió. Cómo lee eso la puerta en la historia es un requisito de su
  ámbito.
- **Cada caso se ejecuta las veces que diga la política**
  ([ADR-0054](0054-the-policy-is-an-optional-file-of-values.es.md)); un caso cuyo veredicto varía se
  marca como inestable, se deja fuera de las cuentas y se informa.

## Base

Leído:

- SWE-bench valida cada tarea por los tests que pasan de fallar a pasar con el parche
  (FAIL_TO_PASS) y los que pasan antes y después (PASS_TO_PASS); una tarea necesita al menos un
  FAIL_TO_PASS, y la validación se repite, quedándose solo con las tareas de resultados consistentes
  ([SWE-bench Goes Live](https://arxiv.org/pdf/2505.23419)).
- En SWE-bench Verified, personas revisaron cada tarea con una rúbrica escrita y etiquetas de
  gravedad, y sus anotadores se formaron con cincuenta tareas etiquetadas de antemano
  ([OpenAI](https://openai.com/index/introducing-swe-bench-verified/)).
- BugsInPy solo conserva un defecto si está en el código fuente, es reproducible y está aislado, y
  dos autores comprobaron el aislamiento por separado
  ([Widyasari et al.](https://www.arxiv.org/pdf/2401.15481)).
- Defects4J excluye los tests que siempre fallan y los que fallan de forma intermitente
  ([Defects4J](https://github.com/rjust/defects4j)).

Medido: la autocomprobación de los tres packs encontró dos testigos en cada uno el 2026-11-15, entre
3, 3 y 6 candidatos, así que hay parches buenos en cada proyecto. Razonamiento, sin test: que una
etiqueta fijada por construcción y comprometida antes de la primera ejecución quita la mayor parte
del sesgo de quien construye el arnés. No lo quita todo: la persona que confirma la etiqueta es
también el mantenedor del arnés.

## Alternativas consideradas

- **Parches escritos por agentes reales.** Más realistas, y con lo que crecerá el conjunto más
  adelante; ningún agente se ejecuta bajo el arnés hasta el bloque C.
- **Etiquetas decididas después de ejecutar.** Ajustarían el arnés a su propia salida.
- **Una segunda persona, independiente, que confirme cada etiqueta.** Mejor; todavía no la hay. Los
  resultados publicados dicen quién etiquetó los casos.
- **Un benchmark público.** Rechazado por la ADR-0030.

## Consecuencias

- Los ficheros de un caso no cambian una vez fusionado; el conjunto solo crece.
- A3 necesita diez casos escritos, aprobados y confirmados antes de que se ejecute su primera
  auditoría.
- Los minutos del mantenedor por caso se conocen desde el primer caso.
- Los resultados publicados dicen que los casos los etiquetó el mantenedor del arnés.
