<!-- translation-of: glossary.md sha256:db286278c747427f -->
# Glosario

*Read in [English](glossary.md).*

Los términos en que se apoyan los invariantes y las decisiones. Un término tiene un solo
significado en todos los documentos; si una decisión necesita otro significado, necesita otro
término.

## El arnés y lo que verifica

| Término | Significado |
|---|---|
| Arnés | Este programa. Corre en la máquina de quien lo usa o en un job de un pipeline, fuera de todo contenedor, y arranca los contenedores que necesita |
| Proyecto verificado | El repositorio cuyo cambio se comprueba. Su código y sus tests corren dentro de un contenedor. El arnés no forma parte de él |
| Pack | Los datos que le dicen al arnés cómo construir el entorno de un proyecto verificado y cómo ejecutar sus tests. No dice nada de cómo se construye el propio arnés |
| Entorno | La imagen de contenedor donde corre el código de un proyecto verificado, construida como dice su pack |
| Preparación | La fase que construye el entorno de un proyecto verificado. Puede descargar sus dependencias |
| Verificación | La fase que ejecuta el código de un proyecto verificado en su entorno, sin red |
| Autocomprobación de un pack | La prueba de que un pack ejecuta de verdad los tests: en un commit pasado del proyecto que arregló un defecto y añadió un test, ese test falla antes del arreglo y pasa después |
| Pipeline del proyecto | La integración continua de un proyecto verificado. Es una fuente para escribir su pack. No es el pipeline donde se prueba el arnés |
| Memoria | Lo que el arnés guarda sobre un proyecto verificado entre ejecuciones: su pack y su política, el contrato de cada cambio, el estado del trabajo. Un almacén propio, en disco local o en su propio repositorio git, nunca dentro del repositorio del proyecto verificado |
| Corpus | Los proyectos verificados y sus cambios, cada uno con un veredicto conocido, que se usan para medir el arnés |

## Contrato y ejemplos

| Término | Significado |
|---|---|
| Contrato | Los requisitos de un cambio y sus ejemplos aprobados, con una huella. Lo aprueba una persona |
| Ejemplo | Una entrada y lo que se espera observar, en una frontera declarada |
| Caso | La etiqueta que agrupa los ejemplos de una misma situación de un requisito |
| Ejemplo aprobado | Un ejemplo que una persona aprobó. Antes de aprobarse es una propuesta |
| Reparto | El momento, al aprobarse el contrato, en que el arnés reserva al azar una parte de los ejemplos aprobados |
| Ejemplo visible | Un ejemplo aprobado que el agente recibe |
| Ejemplo reservado | Un ejemplo aprobado que el reparto apartó. El agente nunca lo recibe |
| Contenido reservado | La entrada o el valor esperado de un ejemplo reservado, **en claro**. La forma cifrada no es contenido reservado |
| Lote sellado | Los ejemplos reservados de un contrato, cifrados, con su semilla y su canario |
| Almacén de lo sellado | Donde se guardan los lotes sellados: un fichero cifrado en el repositorio |
| Ejecución sellada | La ejecución de los ejemplos reservados. Solo ocurre cuando los visibles pasan |

## Lugares

| Término | Significado |
|---|---|
| Sesión de trabajo | Todo lo que el agente puede leer mientras trabaja: el árbol de trabajo, los ficheros de tarea y su propia instalación |
| Directorio de estado del arnés | Donde el arnés guarda el registro, la clave cuando es local, y sus ficheros de trabajo. No forma parte de la sesión de trabajo cuando hay una barrera |
| Barrera al especificar | Lo que separa del agente el sitio donde se especifica un contrato: otra máquina, el envoltorio, otro usuario del sistema, o ninguna. La evidencia la registra |

## Comprobaciones y veredictos

| Término | Significado |
|---|---|
| Comprobación | Una comparación entre lo observado y lo esperado |
| Origen | Quién respalda el resultado esperado de una comprobación: `human`, `derived`, `model` o `existing` |
| Puerta | Un paso del flujo que devuelve un veredicto |
| Estado de trabajo | Un estado del flujo que ejecuta una o más puertas y se cierra con su veredicto agregado |
| Estado de pregunta | Un estado del flujo en el que una persona elige una respuesta de una lista cerrada |
| Presupuesto | Cuántas veces puede repetirse una transición del flujo antes de preguntar a una persona. No termina nada por sí solo. La cantidad está en la política |
| Puerta opcional | Una puerta que la política permite omitir. Todas las demás son obligatorias |
| Veredicto | `PASS`, `FAIL`, `ASK` o `ERROR`. Una puerta devuelve uno; el veredicto de un cambio es su agregación |
| Hallazgo | Un problema encontrado por una comprobación: un código de una lista cerrada, un mensaje, las líneas donde está y el veredicto que da (`FAIL`, `ASK` o `ERROR`) |
| Directiva | Un mapa de un contrato con una clave que empieza por `$`. Es una instrucción para el arnés, no un dato |
| No aplicable | Una puerta que no tiene sobre qué actuar en este cambio, por una condición leída del contrato o del nivel del pack |
| No alcanzada | Una puerta a la que el flujo no llegó, porque una anterior lo detuvo |
| Estado final | Un estado del flujo sin puerta ni transición. O entrega o no entrega |
| Identidad | Quién tomó una decisión humana, junto con cómo se estableció: firmada, declarada, o a través de un cliente y sin verificar |
| Repetición | Recalcular el veredicto de una ejecución desde su registro y sus artefactos guardados, sin preguntar a nadie |
| Entrega | Producir el commit de un cambio y adjuntarle su evidencia. Solo puede hacerlo un estado del flujo que entrega. Hay evidencia de toda ejecución terminada, se entregue o no |
| Respuesta delegada | Una respuesta a una pregunta de la entrevista que una persona dejó a un modelo. Va marcada, y nunca aprueba un ejemplo ni un contrato ni responde a una puerta |
