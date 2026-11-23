<!-- translation-of: 0080-each-example-is-observed-in-a-container-of-its-own.md sha256:da3e1c1ecd58a8a4 -->
# ADR-0080 · Cada ejemplo se observa en un contenedor propio

**Estado:** aceptada

## Contexto

La [ADR-0063](0063-a-program-of-sandbox-observes-the-examples-inside-the-zone.es.md) ejecuta todos
los ejemplos de un lado de una puerta en un contenedor, cada ejemplo en un proceso hijo propio, con
su propio directorio de trabajo. Antes de los casos de B3d que hacen trampa guardando estado entre
llamadas, una sonda preguntó si un ejemplo puede dejarle algo al siguiente en el mismo contenedor.
Corrió sobre el adaptador de podman, con la imagen de los tests de `sandbox`; en cada sonda un primer
ejemplo escribía y un segundo, en otro hijo del mismo contenedor, leía:

| Lo que dejó el primer ejemplo | Lo que encontró el segundo |
|---|---|
| Un fichero en `/tmp`, y en el padre del directorio de trabajo, que es `/tmp` | El fichero |
| Un fichero en `/dokime/out`, el directorio donde el programa principal escribe las observaciones | El fichero |
| Un proceso arrancado con `start_new_session` que escribe un contador | El proceso vivo, con el contador pasando de 12 a 17 |
| Un segmento de memoria compartida de System V y un semáforo, con una clave fija | El texto del segmento y el valor del semáforo |
| Una clave en el llavero del usuario, con `add_key` | Nada: `add_key` y `request_key` dan `ENOSYS` |

`/var/tmp`, `/dev/shm`, `/root`, `/dokime/project`, `/dokime` y `/` no se pudieron escribir. El
programa principal es el proceso 1 del contenedor. Así que, en un contenedor, un ejemplo puede pasar
al siguiente lo que vio, y los ejemplos reservados de la puerta `sealed-examples` se observan en un
contenedor junto con su canario.

## Decisión

Esto enmienda la ADR-0063 en su contenedor para cada lado; el resto se mantiene.

**Cada ejemplo se observa en un contenedor propio.** El adaptador arranca un contenedor para cada
ejemplo de una petición, con la misma imagen, los mismos montajes, límites y garantías
([ADR-0043](0043-tests-run-only-on-an-engine-that-enforces-the-limits.es.md)), y el programa
principal observa en él ese ejemplo solo. Su `/tmp`, su `/dokime/out`, sus procesos y su espacio de
nombres de IPC acaban con él, así que nada de lo que deja un ejemplo llega a otro. Los límites de un
ejemplo, su tiempo y su parte de los bytes de las observaciones, son los de la ADR-0063, que ahora
acotan su contenedor; las observaciones de una petición se leen y se dan en el orden de sus ejemplos,
como antes.

## Base

Comprobado: la sonda de arriba, y el arranque de un contenedor medido en el runner de la CI, veinte
observaciones de un ejemplo, cada una en un contenedor propio a través del adaptador: una mediana de
0,503 segundos, entre 0,497 y 0,614 (#214); en la máquina del mantenedor, entre 0,34 y 0,43.

Medido, el coste sobre el corpus tal como está, con dos ejecuciones sobre la base, una sobre el
cambio y las relaciones: un contenedor por ejemplo en lugar de uno por lado da unos 12 contenedores
más para una auditoría de un contrato de mdformat de 5 ejemplos, unos 30 con sus 3 relaciones, 36
para el contrato de `nextver` de 13 ejemplos y 15 para el de `replace` de 6. A 0,5 segundos, son unos
6, 15, 18 y 7,5 segundos más por caso; sobre los casos de cada trozo, unos 54 segundos más para el
trozo a, hoy 250, y unos 77 para el trozo b, hoy 117. Son cotas superiores, porque una auditoría
puede pararse antes de su última puerta; el trozo c, la reserva a mano y la ejecución sellada, no se
contó y se mide en la primera ejecución.

Solo razonamiento: que no se puede demostrar que una lista de sitios que limpiar entre ejemplos esté
completa, como muestra la memoria compartida de System V, que ningún fichero nombra.

## Alternativas consideradas

- **Limpiar entre ejemplos, dentro del único contenedor.** El programa principal, proceso 1, mataría
  todos los demás procesos tras cada ejemplo y vaciaría `/tmp` y `/dokime/out`. Descartada: cierra
  los sitios sondeados y no los que no se sondearon, y la IPC de System V es uno de ellos; el
  mantenedor decidió que un canal fuera de la lista la descarta.
- **Un espacio de nombres propio para cada hijo**, con `unshare` dentro del contenedor. Descartada:
  necesita una capacidad que el contenedor no tiene ni debe tener.

## Consecuencias

- **Ningún ejemplo ve lo que dejó otro**: las sondas quedan como tests de `sandbox`.
- **Un ejemplo no puede reescribir las observaciones de otro** a través de `/dokime/out` o de un
  proceso que le sobrevive, cosa que un contenedor por lado permitía; que puede reescribir su propia
  observación sigue siendo el límite de la ADR-0063 y de T1 y T2 de la
  [ADR-0010](0010-threat-model.es.md).
- **Cada ejemplo cuesta un contenedor**, alrededor de medio segundo en el runner; el trozo b del job
  `corpus` crece con los casos de B3d, y la ADR-0078 lo vuelve a partir pasados los 6 minutos.
- **Al aceptarse** esta ADR, la ADR-0063 se marca como enmendada por ella.
