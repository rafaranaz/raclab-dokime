---
name: tdd
description: Ciclo TDD de este repositorio. Usar al implementar o cambiar cualquier comportamiento en src/ o tools/, requisito a requisito.
---

# TDD

Cada requisito EARS se construye con el mismo ciclo. El rojo se demuestra; nunca se supone.

## Ciclo

1. **Elige un requisito** de `docs/requirements/<ámbito>.md`. Si no existe, escríbelo antes con la
   skill `requisitos-ears`.
2. **Escribe el test** en `tests/<ámbito>/test_*.py`. La primera línea del fichero declara los
   requisitos que prueba: `# SDD-EARS: CORE-001 CORE-002`.
3. **Ejecútalo y míralo fallar** por la razón correcta.
   - Un rojo legítimo es una aserción de comportamiento que no se cumple.
   - Un `ImportError`, `NameError` o `AttributeError` es un **rojo falso**: el test no llegó a
     ejercitar nada. Declara primero la firma mínima (una función que lanza
     `NotImplementedError`) y vuelve a ejecutar hasta que el fallo sea de comportamiento.
4. **Implementa lo mínimo** que pone el test en verde. Lo que vaya más allá no tiene test que lo
   respalde.
5. **Refactoriza solo en verde.** Con tests en rojo no se puede saber si un cambio rompió algo o ya
   estaba roto.
6. **Ejecuta las puertas** del ámbito antes de commitear: tests, lint, tipos e historia.

## Reglas

- **El verde se consigue en el código de producción, nunca editando el test.** Si el test parece
  equivocado, dilo explícitamente y decide con la persona que revisa; no lo cambies por tu cuenta.
- **Un test prueba comportamiento observable**, no detalles internos: si un refactor sin cambio de
  comportamiento rompe el test, el test estaba mal planteado.
- **Los casos de error también son requisitos.** Cada `If ... then` tiene su test negativo.
- **Un fallo que encuentras al usar el código** se convierte primero en un test que lo reproduce y
  después en un arreglo.
