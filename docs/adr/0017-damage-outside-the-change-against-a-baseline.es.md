<!-- translation-of: 0017-damage-outside-the-change-against-a-baseline.md sha256:75df6377b7c0f23f -->
# ADR-0017 · El daño fuera del cambio se encuentra comparando con una línea base

**Estado:** propuesta

## Contexto

Un cambio puede cumplir su contrato y romper otra cosa. En un estudio, el 30 % de los parches de
un modelo abierto rompía al menos un test que antes pasaba.

## Decisión

- Antes del cambio, la suite existente y todos los ejemplos corren sobre el commit base tantas
  veces como diga la política, dos para empezar. Los tests cuyo resultado varía se marcan como
  inestables, se excluyen y se listan; la lista se guarda en el registro y es una entrada del
  veredicto.
- Después del cambio, todo test que pasaba en la línea base debe seguir pasando y ninguno puede
  desaparecer.
- La proporción de líneas de **producción** cambiadas que ejecutan la suite y los ejemplos debe
  alcanzar el umbral de la política. Las líneas de código de test no cuentan.
- El mapa de qué tests ejecutan qué líneas sale de la cobertura de la línea base. Da al agente una
  lista de tests en riesgo y acota dónde se buscan diferencias de comportamiento.
- Para las diferencias de comportamiento entre base y cambio que ningún requisito explica, un
  modelo las agrupa y propone una explicación; una persona decide.
- Las puertas de ejemplos corren dos veces, en procesos nuevos y en otro orden; un resultado
  distinto pregunta.

## Base

Literatura. Decir al agente qué tests están en riesgo bajó las regresiones del 6,08 % al 1,82 %
([TDAD](https://arxiv.org/abs/2603.17973), 100 casos, un modelo). Los tests antes/después
dirigidos al cambio cubren el 91 % de las líneas cambiadas en bibliotecas Python
([DiffTestGen](https://arxiv.org/abs/2607.16024)); decidir si una diferencia era intencionada
tiene un 58 % de precisión con un modelo ([Testora](https://arxiv.org/abs/2503.18597)), y de ahí
la persona.

## Alternativas consideradas

- **Un grafo de llamadas estático.** Exige análisis por lenguaje dentro del núcleo y es impreciso
  en lenguajes dinámicos. Queda como hipótesis aplazada.
- **Ejecutar solo los tests relacionados con el cambio.** Ahorra tiempo, que aquí no es criterio,
  y deja pasar regresiones.

## Consecuencias

- Esta puerta exige herramientas de cobertura al pack del lenguaje.
- Hay evidencia para bibliotecas; para aplicaciones con interfaz gráfica no se encontró.
