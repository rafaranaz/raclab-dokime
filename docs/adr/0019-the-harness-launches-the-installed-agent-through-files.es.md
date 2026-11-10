<!-- translation-of: 0019-the-harness-launches-the-installed-agent-through-files.md sha256:a2ebd04bc20dbbd1 -->
# ADR-0019 · El arnés lanza el agente instalado y se comunica con él por ficheros

**Estado:** propuesta

## Contexto

Alguien tiene que decidir el orden de los pasos y registrarlos. Si el agente llama al arnés cuando
le parece, el orden depende de un modelo. Cada agente tiene su propia interfaz; los ficheros son
lo único que todos comparten.

## Decisión

- El arnés lanza el agente que el usuario ya tiene, sin su interfaz, con la instalación, la sesión
  y la configuración del usuario.
- La tarea entra como ficheros: los requisitos, los ejemplos visibles, la lista de tests en
  riesgo, el resultado del intento anterior y una plantilla fija. La plantilla le dice al agente
  que pare e impugne cuando un ejemplo contradiga un requisito.
- El resultado es el estado del árbol de trabajo. **El arnés calcula el parche** contra el commit
  base; no se fía de lo que el agente diga.
- El agente puede dejar señales como ficheros (una impugnación, una petición de dependencia,
  notas), validadas contra un esquema.
- El arnés no expone ninguna interfaz de control en red mientras el agente trabaja.
- Lanzar es un puerto. El primer adaptador es el modo sin interfaz propio de cada agente, descrito
  por un perfil que es un dato e incluye cómo se paga el modelo. ACP es el segundo adaptador.
- Un cambio hecho a mano, o por un agente que no se puede lanzar, entra por el modo auditoría.

## Base

Literatura y razonamiento. Dejar que el modelo elija el siguiente paso cuesta entre 2,5 y 17,5
puntos ([STAGE](https://arxiv.org/abs/2608.22538), un estudio). La redacción del prompt y una
salida para pedir ayuda son lo que más reduce las trampas
([ImpossibleBench](https://arxiv.org/abs/2510.20270)). La regla de la interfaz de control sale del
[CVE-2026-82533](https://www.ox.security/blog/cve-2026-82533-deepseek-harness-ai-agent-sandbox-escape/).

## Alternativas consideradas

- **Que el agente llame al arnés como herramienta.** El orden y la cuenta de intentos dependerían
  del agente.
- **Un adaptador escrito en código por agente.** Un perfil como dato hace que un agente nuevo sea
  un fichero nuevo.

## Consecuencias

- Usar una suscripción sin interfaz depende de una política de fabricante que cambió en 2026; la
  forma de pago se registra para que un cambio de política sea un cambio de un campo.
- Los agentes que solo viven dentro de un editor se pueden auditar pero no lanzar.
