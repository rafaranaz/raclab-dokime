<!-- translation-of: 0031-modules-depend-only-on-core.md sha256:9c9bbe4761ba1ba3 -->
# ADR-0031 · Los módulos dependen solo de core; los adaptadores solo los importa la raíz de composición

**Estado:** propuesta

## Contexto

Los módulos se construyen de uno en uno, así que cada uno tiene que poder construirse y probarse
sin los demás. Las dependencias cíclicas preceden a otros problemas de arquitectura entre el 60 %
y el 80 % de los casos estudiados.

## Decisión

- `core` no importa ningún otro módulo. Contiene los tipos, los veredictos, el registro y los
  puertos.
- Los módulos de dominio (`contract`, `oracle`, `evidence`, `packs`) importan solo `core`;
  `oracle` importa además `contract`. Los servicios de dominio (`spec`, `verify`, `delivery`)
  importan esos y no se importan entre sí. `engine` importa los servicios.
- Los adaptadores (`sandbox`, `agents`, `gateway`) importan solo `core` e implementan sus puertos.
  Solo `interfaces`, la raíz de composición, importa adaptadores.
- `evidence` no importa nada más que `core`, para que verificar una evidencia se pueda instalar
  por separado.
- Todo puerto tiene dos adaptadores previstos desde el principio, y toma la forma de un estándar
  existente donde lo hay.
- Estas reglas son contratos de importación comprobados en CI.

## Base

Literatura y práctica. [Estudio de defectos de arquitectura](https://arxiv.org/abs/2203.08702), un
caso industrial.

## Alternativas consideradas

- **Una pila por capas con el motor encima de todo.** El motor se convierte en el sitio donde la
  orquestación se cuela en el código.
- **Importaciones libres sin ciclos.** Cada módulo necesitaría a los demás para probarse.

## Consecuencias

- Más puertos y más cableado en la raíz de composición.
- Un puerto con un solo adaptador es una suposición, y se trata como tal.
