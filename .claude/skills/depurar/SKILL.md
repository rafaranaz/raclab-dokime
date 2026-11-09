---
name: depurar
description: Diagnóstico estructurado de un fallo (test rojo inesperado, check de CI que falla, error en ejecución). Usar antes de cambiar código para arreglarlo.
---

# Depurar

Ante un fallo, el error más caro es empezar a cambiar cosas. Cada cambio a ciegas añade una
variable y complica el siguiente diagnóstico.

1. **Reproduce primero.** Un fallo que no sabes reproducir no lo sabes arreglar: solo sabrás que
   dejó de manifestarse. La reproducción acaba siendo un test.
2. **Lee el error entero**, incluida la traza completa. La primera línea suele ser la causa; la
   última, solo dónde explotó.
3. **Formula una hipótesis falsable** y escríbela: «creo que X porque Y».
4. **Haz un solo cambio para comprobarla.** Si cambias tres cosas y funciona, no sabes cuál fue, y
   las otras dos se quedan en el código para siempre.
5. **Si la hipótesis falla, descártala explícitamente** y formula otra. No apiles una nueva encima.
6. **Cuando funcione, explica por qué.** Un arreglo que funciona sin saber por qué es un fallo
   latente.
7. **Deja el test de regresión** junto al arreglo, en el mismo commit `fix`, con el porqué en el
   cuerpo del mensaje.

Señal de alarma: si llevas varios intentos con el mismo arreglo ligeramente retocado, la hipótesis
es incorrecta. Vuelve al paso 2 y relee lo que el sistema te está diciendo.
