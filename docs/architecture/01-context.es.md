<!-- translation-of: 01-context.md sha256:d91ce48eff068148 -->
# Contexto y zonas de confianza

*Read in [English](01-context.md).*

## Con quién habla el sistema

raclab-dokime es una orden que corre en la máquina de una persona y, con el mismo código, en un
ejecutor de CI. No tiene servidor propio.

```mermaid
flowchart LR
    person["Persona<br/>escribe y aprueba el contrato,<br/>responde preguntas"]
    reviewer["Revisor<br/>aprueba el pull request"]

    subgraph system["raclab-dokime"]
        cli["Orden y motor de flujo"]
    end

    agent["Agente de programación<br/>el que el usuario ya tiene"]
    model["Modelo<br/>API alojada o servidor local"]
    engine["Motor de contenedores"]
    registry["Registros de paquetes"]
    forge["Forja de git<br/>GitHub primero"]
    ci["Ejecutor de CI"]
    signer["Agente de claves<br/>del sistema"]

    person -->|contrato, aprobaciones, respuestas| cli
    cli -->|preguntas, informes| person
    cli -->|ficheros de tarea, árbol de trabajo| agent
    agent -->|inferencia| model
    cli -->|llamadas estructuradas| model
    cli -->|construir imagen, ejecutar aislado| engine
    engine -->|instalar, solo al preparar| registry
    cli -->|huella a firmar| signer
    cli -->|rama, evidencia| forge
    forge -->|pull request| reviewer
    forge -->|dispara| ci
    ci -->|la misma orden, modo auditoría| cli
```

Tres cosas que fija el diagrama:

- El agente es **externo**. El arnés le entrega ficheros y lee el árbol de trabajo de vuelta. No
  conoce su protocolo interno ni su modelo.
- El arnés hace sus propias llamadas a un modelo por una vía separada del agente
  ([ADR-0022](../adr/0022-model-calls-of-the-harness-go-through-a-port.es.md)).
- CI ejecuta **el mismo programa** en modo auditoría. No hay una segunda implementación de las
  puertas.

## Zonas de confianza

```mermaid
flowchart TB
    subgraph host["zona anfitrión: de confianza"]
        harness["motor, oráculo, registro"]
        human["canal humano"]
    end
    subgraph ci["CI: de confianza, no controlado por el autor durante la ejecución"]
        key["clave de los lotes sellados"]
    end
    subgraph prepare["zona de preparación: red solo hacia registros"]
        build["construcción de la imagen"]
    end
    subgraph work["zona de trabajo: sin confianza"]
        agent["agente de programación"]
        tree["árbol de trabajo, ficheros de tarea, ficheros de señal"]
    end
    subgraph verify["zona de verificación: código sin confianza, sin red"]
        subject["commit base más parche"]
        probe["sonda, proceso o servicio"]
    end
    model["modelo"]
    registries["registros de paquetes"]

    harness -->|requisitos, ejemplos visibles| tree
    tree -->|parche calculado por el arnés| harness
    agent --> model
    build -->|a través de un intermediario de credenciales| registries
    build -->|huella de la imagen| harness
    harness -->|parche, entradas de los ejemplos| subject
    probe -->|observaciones| harness
    key -.->|nunca en la máquina de un desarrollador| work
```

| Zona | Qué corre | Red | Ve secretos | Ve ejemplos reservados |
|---|---|---|---|---|
| Anfitrión | El arnés | La del usuario | A través del agente de claves | Solo donde está la clave: CI, o la máquina de un desarrollador solo |
| Preparación | La construcción de la imagen | Registros permitidos, por un intermediario | No | No |
| Trabajo | El agente | La suya, o filtrada cuando el envoltorio está activo | La sesión del agente | No |
| Verificación | El código escrito por el agente | Ninguna | No | Solo las **entradas** |

Qué cruza cada frontera:

- De anfitrión a trabajo: requisitos, ejemplos visibles, la lista de tests en riesgo,
  realimentación.
- De trabajo a anfitrión: el árbol de trabajo, del que el arnés calcula el parche, y ficheros de
  señal leídos como datos.
- De anfitrión a verificación: el commit base, el parche filtrado y entradas.
- De verificación a anfitrión: observaciones y ficheros de resultados, leídos como datos.

Dos puntos a tener a la vista:

- Aislar la zona de trabajo **protege la máquina y los secretos del usuario**. La corrección del
  veredicto no depende de ello: depende de que la verificación parta del commit base y de que los
  valores esperados no entren en la zona de verificación. Por eso aislar al agente es opcional y
  la verificación no
  ([ADR-0020](../adr/0020-agent-isolation-is-optional-adoption-is-a-ladder.es.md)).
- Qué se defiende y qué no está en el modelo de amenazas
  ([ADR-0010](../adr/0010-threat-model.es.md)).
