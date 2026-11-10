<!-- translation-of: 0010-threat-model.md sha256:90613edfbdb5f864 -->
# ADR-0010 · El modelo de amenazas dice qué se defiende y qué no

**Estado:** propuesta

## Contexto

Sin un modelo de amenazas nadie puede juzgar si un nivel de aislamiento basta ni cuánto vale una
evidencia. En 2026 se escapó de un arnés con las mismas técnicas de aislamiento a través de su
propia interfaz de control local
([CVE-2026-82533](https://www.ox.security/blog/cve-2026-82533-deepseek-harness-ai-agent-sandbox-escape/)).

## Decisión

| Id | Amenaza | En alcance | Defensa principal |
|---|---|---|---|
| T1 | Agente descuidado: toca lo que no debe, rompe tests existentes | Sí | Verificación sobre árbol limpio, puerta de regresión |
| T2 | Agente oportunista: ajusta la solución a lo que ve | Sí | Comparación fuera del proceso del sujeto, ejemplos reservados |
| T3 | Contenido del repositorio o de una dependencia que inyecta instrucciones | En parte | Aislamiento opcional; la verificación no lee instrucciones |
| T4 | Paquete inventado o malicioso pedido como dependencia | En parte | Fase de preparación con registros permitidos y aprobación humana |
| T5 | Código hostil dirigido contra el propio arnés | No | Se declara en la evidencia |
| T6 | Un usuario que falsea su propia evidencia en local | No | Repetición de la verificación en CI |
| T7 | Un proveedor de modelo comprometido | No | Un modelo local lo evita |

Activos, por orden: la máquina y las credenciales del usuario, el contenido reservado, la integridad
del veredicto, la integridad de la evidencia.

## Base

Razonamiento, más un incidente. Las cuatro técnicas de T2 son las medidas en
[ImpossibleBench](https://arxiv.org/abs/2510.20270).

## Alternativas consideradas

- **No declararlo.** Toda decisión posterior sobre aislamiento se discutiría sin criterio.
- **Poner T5 en alcance.** Exige un entorno endurecido en cada verificación, lo que contradice
  funcionar en la máquina de un desarrollador sin fricción.

## Consecuencias

- La suite de tests que ya tiene el proyecto corre dentro del proceso del código examinado, así
  que solo resiste T1 y parte de T2; la evidencia la marca con su propio origen.
- Quien necesite cubrir T5 o T6 tiene que añadir controles fuera de este producto.
