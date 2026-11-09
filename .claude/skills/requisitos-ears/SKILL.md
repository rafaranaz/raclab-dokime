---
name: requisitos-ears
description: Escribir o revisar requisitos EARS en docs/requirements/. Usar al abrir un ámbito, antes de escribir cualquier test o código.
---

# Requisitos EARS

EARS existe para quitar la ambigüedad de los requisitos en prosa. Cada requisito usa una de estas
cinco plantillas, y ninguna otra:

| Tipo | Plantilla | Cuándo |
|---|---|---|
| Ubicuo | `The <component> shall <response>.` | Siempre cierto, sin disparador |
| Por evento | `When <trigger>, the <component> shall <response>.` | Reacción a algo que ocurre |
| Por estado | `While <state>, the <component> shall <response>.` | Vigente durante un estado |
| No deseado | `If <unwanted condition>, then the <component> shall <response>.` | Errores y casos límite |
| Opcional | `Where <feature is present>, the <component> shall <response>.` | Depende de la configuración |

Se admite combinar estado y evento: `While <state>, when <trigger>, the <component> shall <response>.`

## Formato en este repositorio

En `docs/requirements/<ámbito>.md`, un requisito por línea, en inglés:

```
- **GRAPH-004** If a reference matches more than one symbol, then the resolver shall emit no edge with confidence 1.0.
```

- Identificador: el ámbito en mayúsculas, un guion y tres dígitos. No se reutilizan identificadores
  retirados.
- Se pueden agrupar bajo encabezados en español.

## Reglas que hacen que valgan algo

- **Un requisito, un comportamiento verificable.** Si necesitas «and» para unir dos respuestas
  distintas, son dos requisitos. `tools/check_ears.py` rechaza más de un `shall`.
- **La respuesta se observa desde fuera.** «Shall validate correctly» no es verificable; «shall
  reject the request with an error naming the field and leave the state unchanged» sí.
- **Los casos no deseados no son opcionales.** Un requisito sin su `If ... then` deja sin
  especificar la ruta de error, que es justo por donde se cuelan los defectos.
- **Nada de adverbios de calidad sin métrica.** «Fast», «robust», «efficient» no caben; si hay un
  límite, se escribe con su número. El check rechaza una lista de términos vagos.
- **Cada requisito tiene al menos un test** que lo declara en su marcador `# SDD-EARS:`.

## Antes de dar los requisitos por buenos

- Léelos como si fueras quien implementa: ¿podrías escribir el test sin preguntar nada?
- Busca el caso de error de cada evento y el valor límite de cada umbral.
- Pásalos por `uv run python -m tools.check_ears`.
