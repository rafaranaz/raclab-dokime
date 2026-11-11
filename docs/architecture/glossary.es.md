<!-- translation-of: glossary.md sha256:6372c977ccfd1e2d -->
# Glosario

*Read in [English](glossary.md).*

Los términos en que se apoyan los invariantes y las decisiones. Un término tiene un solo
significado en todos los documentos; si una decisión necesita otro significado, necesita otro
término.

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
| Presupuesto | Cuántas veces puede repetirse una transición del flujo antes de preguntar a una persona. La cantidad está en la política |
| Puerta opcional | Una puerta que la política permite omitir. Todas las demás son obligatorias |
| Veredicto | `PASS`, `FAIL`, `ASK` o `ERROR`. Una puerta devuelve uno; el veredicto de un cambio es su agregación |
| No aplicable | Una puerta que no tiene sobre qué actuar en este cambio, por una condición leída del contrato o del nivel del pack |
| No alcanzada | Una puerta a la que el flujo no llegó, porque una anterior lo detuvo |
| Estado final | Un estado del flujo sin puerta ni transición. O entrega o no entrega |
| Identidad | Quién tomó una decisión humana, junto con cómo se estableció: firmada, declarada, o a través de un cliente y sin verificar |
| Repetición | Recalcular el veredicto de una ejecución desde su registro y sus artefactos guardados, sin preguntar a nadie |
| Entrega | Producir el commit de un cambio y adjuntarle su evidencia. Solo puede hacerlo un estado del flujo que entrega. Hay evidencia de toda ejecución terminada, se entregue o no |
| Respuesta delegada | Una respuesta a una pregunta de la entrevista que una persona dejó a un modelo. Va marcada, y nunca aprueba un ejemplo ni un contrato ni responde a una puerta |
