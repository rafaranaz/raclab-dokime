<!-- translation-of: 0037-a-contract-is-read-by-strict-rules-of-its-own.md sha256:b1a76dfcb5b3640d -->
# ADR-0037 · Un contrato se lee con reglas estrictas propias, y se informa de todos los problemas

**Estado:** aceptada

## Contexto

El hito A1 valida un fichero de contrato y dice qué le falta. Un contrato se firma por su huella,
así que lo que lee el validador tiene que ser lo que leyó la persona. YAML no da eso por sí solo.
Una clave repetida conserva uno de sus valores. Un valor sin comillas cambia de tipo según el
lector: `no` pasa a ser un booleano en algunos, `1.10` pasa a ser el número 1.1, `010` pasa a ser
10, `2026-11-10` pasa a ser una fecha. Un texto escrito en varias líneas se une con espacios salvo
que sea un bloque literal, y que un bloque literal acabe o no en salto de línea depende de un guion
(`|` o `|-`). Un alias o una clave de fusión hace que un sitio del fichero signifique lo que dice
otro.

## Decisión

- **La biblioteca solo analiza.** Un contrato, y un fichero de flujo, se analiza con PyYAML hasta
  sus eventos y su árbol de nodos. Lo que significa cada nodo lo deciden las reglas de abajo, no
  la biblioteca.
- **Un subconjunto llano.** Un solo documento. Sin anclas, alias, etiquetas ni claves de fusión.
- **Claves.** Una clave es un texto, comparado tal como está escrito. Una clave que se repite
  dentro de un mapa es un hallazgo, y también un `id` que se repite entre los requisitos, los
  ejemplos o las relaciones. El hallazgo nombra todas las líneas donde aparece.
- **Valores sin comillas.** `true` y `false` son booleanos, `null` es nulo, y un número escrito
  como lo escribe JSON es un número. Un valor que algún lector de YAML leería con otro tipo se
  rechaza pidiendo comillas: `yes`, `no`, `on`, `off`, `y`, `n`, `~`, un valor vacío, un número
  con ceros a la izquierda, con guiones bajos, con `+` delante o con el punto suelto, las formas
  hexadecimal y octal, los infinitos, las fechas y las horas. Un número cuyos decimales acaban en
  cero, como `1.10`, se rechaza igual. Todo lo demás es un texto. Un valor entre comillas es
  siempre un texto.
- **Textos de varias líneas.** Un escalar que ocupa más de una línea del fichero tiene que ser un
  bloque literal (`|`) cuyo valor acabe en exactamente un salto de línea. Se rechazan el bloque
  plegado (`>`), el bloque con `|-` y el escalar, con o sin comillas, que continúa en la línea
  siguiente. También una línea de un bloque literal que acabe en espacio o tabulador.
- **Todos los problemas en una ejecución.** La comprobación informa de todos los hallazgos, cada
  uno con un código de una lista cerrada y sus líneas, incluidos los hallazgos cuyo veredicto
  descarta la agregación. Una comprobación que necesita una parte que otra anterior rechazó no se
  ejecuta sobre esa parte. Un fichero que no es YAML, o que tiene un alias, detiene las
  comprobaciones siguientes.
- **Veredictos.** Un fichero que rompe estas reglas da `FAIL`. Un fichero que no se puede abrir
  da `ERROR`.

## Base

Comprobado ejecutando código (PyYAML 6.0.3, `ruamel.yaml` 0.19.1, `strictyaml` 1.6.2) y un
prototipo del lector:

- PyYAML conserva la última de dos claves iguales y no avisa, y lee `on` y `no` como booleanos.
- `ruamel.yaml` en YAML 1.2 deja `no` como texto, pero sigue leyendo `1.10` como 1.1, `010` como
  10, `1_000` como 1000, `2026-11-10` como una fecha y un valor vacío como nulo. Acepta alias y
  claves de fusión, y mantiene `1` y `'1'` como dos claves distintas.
- Las dos bibliotecas dan, para cada escalar, su estilo (sin comillas, con comillas, `|`, `>`) y
  su primera y última línea. No dan el guion de `|-`, pero el valor lo delata. Un bloque `|+` sin
  líneas en blanco detrás da el mismo valor que `|`.
- El prototipo, con PyYAML solo como analizador, informa de cada clave repetida con todas sus
  líneas, de cada valor rechazado y de cada texto rechazado en una sola ejecución. Sobre los tres
  contratos escritos a mano del hito A0 encontró los siete bloques `|-` y un valor en el que
  nadie había reparado: una cabecera de tabla `n`.
- `strictyaml` rechaza claves repetidas, alias y tipos implícitos, y también el estilo de flujo
  (`{a: 1}`, `[1, 2]`) que usan todos los contratos.
- La especificación YAML 1.2.2 dice que las claves de un mapa son únicas, y que el que dos claves
  sean iguales depende del esquema.
- PyYAML y `ruamel.yaml` han tenido una versión en los últimos catorce meses.

De memoria, sin comprobar hoy: que la lista de tipos de YAML 1.1 cuenta `y` y `n` como booleanos,
y que las reglas para los valores sin comillas se parecen al esquema JSON de la especificación
YAML 1.2. No se han mirado enlaces a otros analizadores. Razonamiento: con reglas propias el
significado de un contrato no cambia si cambia la biblioteca; la regla de los decimales acabados
en cero; informar de todo a la vez, que le ahorra a la persona una vuelta por problema. La prueba
que confirma el conjunto es el criterio de A1, un conjunto de contratos con defectos sembrados
donde hay que informar de todos.

## Alternativas consideradas

- **Fiarse de los tipos de `ruamel.yaml` en YAML 1.2.** Quita la trampa del `no` y deja las demás
  de la lista de arriba.
- **`strictyaml`.** Tiene la filosofía correcta y la superficie equivocada: sin el estilo de
  flujo, un ejemplo de tres líneas ocupa quince.
- **Otro formato, JSON o TOML.** JSON no tiene comentarios y escribe un texto de varias líneas
  como una línea con escapes; TOML es incómodo para listas de ejemplos anidados. Los dos quitan
  las trampas quitando lo que hace legible un contrato. Esto es razonamiento, no una prueba.
- **Parar en el primer problema.** Más sencillo de escribir. Cada ejecución revelaría un
  problema.

## Consecuencias

- PyYAML pasa a ser una dependencia de ejecución. Solo se usa su analizador.
- El lector vive en `core`, porque lo usan `contract` y el cargador de flujos
  ([ADR-0035](0035-the-flow-is-loaded-and-validated-in-core.es.md)). Recibe texto; no abre
  ficheros.
- Los tres contratos de A0 se reescriben con estas reglas antes de entrar en el corpus.
- Quien quiera el texto `no` o `1.10` lo escribe entre comillas, y el validador se lo dice.
