<!-- translation-of: 0007-mit-license.md sha256:54b330cd06c1b853 -->
# ADR-0007 · Licencia MIT

**Estado:** aceptada

## Contexto

`dokime` se publicó bajo la Business Source License 1.1, que protege el uso comercial durante un
periodo antes de convertirse en una licencia de código abierto. El mercado para un harness como
este es hoy limitado, y el principal valor de publicarlo es que quien lo encuentre útil pueda
adoptarlo, adaptarlo o aprender de él sin fricción.

## Decisión

`raclab-dokime` se publica bajo la licencia MIT.

## Alternativas descartadas

- **Business Source License 1.1, como en `dokime`.** Protege una oportunidad comercial que hoy no
  existe a costa de desanimar la adopción y las contribuciones.
- **Apache License 2.0.** Igual de permisiva y con una concesión explícita de patentes, pero más
  larga y con más obligaciones para quien la redistribuye; MIT basta para el objetivo de máxima
  reutilización.

## Consecuencias

- Cualquiera puede usar, modificar y redistribuir el código, también con fines comerciales, siempre
  que mantenga el aviso de copyright.
- Pasar más adelante a una licencia más restrictiva solo afectaría al código nuevo, no a lo ya
  publicado bajo MIT.
