---
name: adr
description: Redactar un ADR en docs/adr/. Usar cuando se toma una decisión con consecuencias sobre la arquitectura, las herramientas o el proceso.
---

# ADR

Un ADR documenta una decisión con consecuencias, no un resumen de lo hecho. Si al leerlo dentro de
un año no se entiende por qué **no** se eligió la alternativa, el ADR ha fallado.

## Cuándo escribir uno

- Se elige entre alternativas reales y la elección condiciona trabajo futuro.
- Se cambia una regla de proceso o una puerta de CI.
- Se acepta una limitación conocida.

No hace falta para cambios cuyo porqué cabe en el mensaje de commit.

## Formato

Fichero `docs/adr/NNNN-titulo-en-minusculas.md`, con el siguiente número libre, y una fila nueva en
el índice `docs/adr/README.md`.

```markdown
# ADR-NNNN · Título que nombra la decisión

**Estado:** propuesta | aceptada | sustituida por ADR-MMMM

## Contexto
Las fuerzas en juego: restricciones reales y evidencia, no deseos.

## Decisión
Lo que se elige, en presente y en voz activa («Usamos X»).

## Alternativas descartadas
Al menos una, cada una con la razón concreta por la que se descartó.

## Consecuencias
Lo bueno y lo malo. Toda decisión tiene un coste; si no lo encuentras, no has entendido la decisión.
```

## Reglas

- **Un ADR, una decisión.** Si el título lleva una «y», son dos.
- **Los ADR aceptados no se editan, se sustituyen.** Cambiar de opinión es legítimo; reescribir la
  historia inutiliza el registro. Lo único que se toca en un ADR antiguo es su estado.
- **No repitas lo que el código ya dice.** El ADR recoge lo que el código no puede decir: por qué
  esto y no aquello.
- **Un ADR nace como `propuesta`** y pasa a `aceptada` cuando su PR se aprueba.
