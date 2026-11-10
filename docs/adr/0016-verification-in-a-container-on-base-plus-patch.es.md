<!-- translation-of: 0016-verification-in-a-container-on-base-plus-patch.md sha256:6ecf2d8ccc1106ea -->
# ADR-0016 · La verificación corre en un contenedor sin red, sobre el commit base más el parche

**Estado:** aceptada

## Contexto

Si el cambio se verifica en el entorno donde trabajó el agente, cualquier cosa que el agente haya
dejado allí (un paquete instalado, un fichero en caché, el ejecutor de tests modificado) puede
hacer que las comprobaciones pasen.

## Decisión

- La verificación parte del commit base, aplica el parche que calcula el arnés y corre en un
  contenedor **sin red**. Un motor de contenedores es requisito del producto.
- Tres fases con red distinta: *preparar* alcanza solo los registros de paquetes permitidos;
  *trabajar* es la del agente; *verificar* no alcanza nada.
- Las credenciales de registros privados las añade desde fuera un intermediario. Nunca entran en
  la imagen.
- Una dependencia nueva no se instala durante el trabajo. El agente la pide; el arnés enseña que
  el paquete existe en un registro permitido, su antigüedad y el cambio en el fichero de bloqueo;
  una persona aprueba; la fase de preparar se repite.
- Las rutas protegidas incluyen los tests, su configuración y el directorio del arnés. Un cambio
  en ellas se descarta del parche salvo que el contrato lo autorice, y el intento sigue.
- Los servicios que los tests necesitan corren junto al código dentro de la red aislada y se
  reinician antes de cada verificación. Los tests que necesitan red externa se excluyen y se
  declaran.
- Toda ejecución parte de la imagen: nada de lo que una ejecución escribe la sobrevive, salvo las
  observaciones y los ficheros de resultados que devuelve. El entorno registra qué montó y qué
  pasó a la zona de verificación.

## Base

Razonamiento y práctica documentada. Montar un entorno automáticamente funciona entre el 17 % y
el 38 % de las veces y el 12,7 % de los resultados son falsos aprobados
([Multi-Docker-Eval](https://arxiv.org/abs/2512.06915)), y por eso la línea base del
[ADR-0017](0017-damage-outside-the-change-against-a-baseline.es.md) es obligatoria.

## Alternativas consideradas

- **Verificar con un envoltorio ligero en la máquina del usuario.** No hay entorno limpio, y el
  código examinado comparte el anfitrión.
- **Preparar sin credenciales.** Los equipos instalan desde registros privados.

## Consecuencias

- Docker, Podman o similar tiene que estar instalado donde corra la verificación. Un equipo puede
  verificar solo en CI y no necesitar nada en local.
- Los tests se ejecutan dos veces: por el agente mientras trabaja, y aquí.
