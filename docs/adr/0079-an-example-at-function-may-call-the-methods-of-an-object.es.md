<!-- translation-of: 0079-an-example-at-function-may-call-the-methods-of-an-object.md sha256:6f36e810681127e3 -->
# ADR-0079 · Un ejemplo en function puede llamar a los métodos de un objeto

**Estado:** propuesta

## Contexto

La [ADR-0039](0039-what-a-contract-of-the-first-version-may-say.es.md) permite que un ejemplo en
`function` llame en cada paso a un objetivo `module:function` con valores JSON, y espere un valor
JSON o una excepción. De los 41 testigos del corpus, 21 no son expresables así. B3c leyó esos 21 dos
veces frente a cuatro opciones, fijadas antes de las lecturas, y el mantenedor resolvió los seis
pares que las lecturas etiquetaron distinto (#206, `tests/corpus/boundary/`). De los 18 testigos que
los dos lectores nuevos de B3a etiquetan como aislados, 9 son expresables hoy; cada opción los
dejaría en:

| Opción | Testigos aislados expresables, de 18 | Entre los 9 no expresables hoy |
|---|---|---|
| (a) llamadas sobre un objeto | 11 | W07, W34 |
| (b) una sesión de Python | 17 | todos menos W15 |
| (c) fixtures del paquete | 13 | W07, W32, W34, W39 |
| (d) no ampliar | 9 | — |

W07 y W34 son arreglos de python-semver que hoy un contrato no puede recoger: los operadores de
comparación de un `Version` con una colección mal formada, y `Version.next_version` con un token
propio. Los dos necesitan un objeto construido por una llamada y un método suyo llamado después.
Hoy cada paso de un ejemplo en `function` llama al mismo objetivo, y de un valor que no es JSON solo
se registra el nombre de su tipo.

## Decisión

Esto enmienda la ADR-0039 en lo que puede decir un ejemplo en `function`; el resto se mantiene.

**Un ejemplo en `function` puede llamar a los métodos del objeto que devuelve su primer paso:**

- **Un paso posterior puede nombrar un método** con `call` en su entrada: llama a ese método, por su
  nombre, sobre lo que devolvió el primer paso, con `args` y `kwargs` JSON. Un método dunder es un
  método, así que se pueden llamar `__eq__`, `__getitem__` o `__len__`. Un paso sin `call` llama al
  objetivo, como hoy; el primer paso nunca lleva `call`.
- **`call` nombra un método público**: `contract check` rechaza, con el veredicto `FAIL`, un nombre
  que empieza por un guion bajo, salvo que empiece y acabe por dos, como un método dunder.
- **Cada paso con `call` se ejecuta dé lo que den los pasos anteriores**, como doctest ejecuta cada
  ejemplo de un docstring: una llamada que lanza da su excepción a su propia expectativa, y las
  llamadas siguientes se ejecutan sobre el mismo objeto.
- **Un valor que no es JSON se puede esperar por su `repr`**, con el matcher `$repr` en `returns`: se
  cumple cuando el valor observado no es un valor JSON y su `repr` es el texto dado. Un valor JSON se
  compara como valor JSON, nunca por su `repr`.
- **`contract check` rechaza un `$repr` que contiene una dirección de memoria**, un texto con
  ` at 0x`, con el veredicto `FAIL`, porque cambiaría en cada ejecución, y un `$repr` más largo que
  los 1.000 caracteres de un `repr` que guarda una observación.
- **Un `repr` observado de más de 1.000 caracteres** se guarda cortado, con una marca de que se
  cortó; entonces es más largo que cualquier texto que pueda dar un `$repr`, así que `$repr` no se
  cumple, y el paso falla como cualquier expectativa que no se cumple. No es `ERROR` ni `ASK`: se sabe
  que lo observado difiere de lo que espera el contrato, así que nada queda sin decidir, y el
  contrato no se equivocó al esperarlo.
- **Cuando el primer paso no devuelve nada**, porque lanza una excepción, los pasos posteriores que
  nombran un método no se ejecutan, y el ejemplo se observa con los pasos que ejecutó.
- **Ningún código de quien escribe el contrato**: ningún ejemplo define una clase, una función, un
  decorador ni un mock; sus entradas siguen siendo valores JSON.

## Base

Comprobado: el recuento de #206, que un test del corpus recalcula a partir de las dos lecturas y la
resolución.

Buscado fuera, y cómo escribe cada herramienta ejemplos que construyen un objeto y llaman a sus
métodos: doctest ejecuta los ejemplos de un docstring en una copia superficial de los globales del
módulo, así que un nombre ligado en un ejemplo lo ve el siguiente
([doctest](https://docs.python.org/3/library/doctest.html)); Hypothesis escribe las pruebas con
estado como una máquina cuyas reglas son llamadas sobre el sistema bajo prueba, con su estado en la
máquina o en *bundles* ([stateful tests](https://hypothesis.readthedocs.io/en/latest/stateful.html));
la ActionFixture de FitNesse construye un objeto con `start` y llama a sus métodos por su nombre con
`enter`, `press` y `check`, desde una tabla que sigue siendo datos, mientras que el código que
necesita se escribe aparte en fixtures
([ActionFixture](https://fitnesse.org/FitNesse/UserGuide/FixtureGallery/BasicFitFixtures/ActionFixture.html));
FitNesse dice que la ha sustituido DoFixture
([DoFixture](https://fitnesse.org/FitNesse/UserGuide/FixtureGallery/FitLibraryFixtures/DoFixture.html)).
La opción a es la tabla de ActionFixture sin fixtures; la opción c las añadiría; la opción b es
doctest. No se encontró ningún estudio que compare el coste de revisar ejemplos escritos como código
con el de ejemplos escritos como datos.

Solo razonamiento, sin medir: el coste en pull requests, y que revisar código le cuesta al
mantenedor más que revisar datos; la revisión de los contratos de B0, unos 4 minutos cada uno, fue de
ejemplos que son datos.

## Alternativas consideradas

- **(b) Una sesión de Python.** Descartada: deja entrar 17 de los 18 testigos aislados, pero un
  ejemplo pasa a ser código que el mantenedor revisa como un test, en contra de un contrato hecho de
  datos.
- **(c) Fixtures del paquete.** Ahora no: añade W32 y W39, los dos de cachetools, a costa de un
  módulo de código en el paquete y dos o tres pull requests más. Queda como posible ampliación sobre
  esta si los casos de B3d la piden, con la regla ya decidida de lo que contiene una fixture: solo lo
  que definiría quien usa la biblioteca para usarla, nunca lógica de comprobación.
- **(d) No ampliar.** Descartada: la mitad de los testigos aislados se queda fuera.

## Consecuencias

- **W07 y W34 pueden ser casos buenos** de la frontera `function` en B3d, y también W13 y W14, que
  la ADR-0074 no etiqueta como aislados.
- **El formato del contrato se ata más a Python** en `function`: métodos dunder y `repr`. La frontera
  `function` ya era de Python; `cli`, la frontera de la sonda de un segundo lenguaje que decide el
  cierre del bloque B, no cambia.
- **Un `repr` puede cambiar entre versiones del proyecto**, así que un ejemplo que espera uno puede
  fallar por un cambio que no es una regresión; es un límite, y `$repr` es para valores que JSON no
  puede contener.
- **Las palabras para el agente** siguen sin dar ningún valor: un paso que no cumple un `$repr` dice
  que el valor difiere, no el texto.
- **Una llamada actúa siempre sobre lo que devolvió el primer paso**, nunca sobre lo que devolvió una
  llamada anterior: las llamadas no se encadenan, así que no se puede llamar a un método de un objeto
  que devuelve una llamada; es un límite.
- **Una relación sigue ejecutándose solo sobre fuentes de un paso**, así que un ejemplo con llamadas
  nunca es una fuente
  ([ADR-0076](0076-a-relation-runs-on-the-visible-examples-of-its-requirement.es.md)).
- **Al aceptarse** esta ADR, la ADR-0039 se marca como enmendada por ella.
