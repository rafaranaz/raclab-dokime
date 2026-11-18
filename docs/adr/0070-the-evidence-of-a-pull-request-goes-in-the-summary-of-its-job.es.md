<!-- translation-of: 0070-the-evidence-of-a-pull-request-goes-in-the-summary-of-its-job.md sha256:c85a427071457d97 -->
# ADR-0070 · La evidencia de una pull request va en el resumen de su job y en un artefacto

**Estado:** propuesta

## Contexto

A4 ejecuta `audit` en cada pull request de este repositorio y tiene que mostrar su resultado al
mantenedor antes de la fusión. El código del cambio se ejecuta en ese job, dentro de los
contenedores de la verificación, y los mensajes de los hallazgos citan texto que dokime no escribió
([ADR-0064](0064-the-evidence-of-a3-is-an-unsigned-statement-with-a-closed-predicate.es.md)). La
evidencia no se firma hasta el bloque E.

## Decisión

**La regla.** La evidencia de una auditoría en CI llega a la persona que fusiona, y el workflow que
ejecuta el código del cambio no tiene ningún derecho a escribir en el repositorio.

**El mecanismo en A4.**

- **El workflow se ejecuta en `pull_request`**, solo con el permiso `contents: read`, y nunca en
  `pull_request_target`.
- **El resumen del job** muestra solo los campos que fija dokime: el veredicto, el story, la huella
  del contrato, cada puerta con su estado y su veredicto, los códigos de los hallazgos y la huella de
  la evidencia. Los mensajes, que pueden citar el código del cambio, no se muestran ahí.
- **El fichero de la evidencia y el registro** se suben como artefacto del job.
- **No se escribe nada en la pull request.** Un comentario, cuando se quiera, es un segundo workflow
  ejecutado por `workflow_run`, con el permiso de escribir y sin el código del cambio.

## Base

Comprobado en la documentación de GitHub: un workflow ejecutado por `pull_request` desde un fork
recibe un token que solo puede leer, y uno ejecutado por `pull_request_target` recibe un token que
puede escribir, incluso para un fork
([el token de GitHub](https://docs.github.com/fr/enterprise-server@3.13/actions/reference/github_token-reference)).
Lo escrito sobre su riesgo aconseja ejecutar el código de un fork solo en `pull_request`
([SonarSource](https://rules.sonarsource.com/githubactions/RSPEC-7631)).

Buscado y no encontrado: cuánto tiempo guarda GitHub un artefacto por defecto.

Razonamiento, sin prueba: los campos del resumen son nombres, veredictos, códigos y huellas que el
lector de la evidencia comprueba contra sus patrones, así que no necesitan escaparse, y un mensaje
que cita el código del cambio se queda en el artefacto. La prueba es la primera pull request de A4
que lleve su evidencia.

## Alternativas consideradas

- **Un comentario en la pull request.** Necesita el permiso de escribir. Hecho de forma segura, es un
  segundo workflow, que se guarda para cuando se quiera un comentario.
- **Una atestación con `actions/attest`**, que acepta un tipo de predicado propio. Firma con la
  identidad del workflow, que es la independencia `ci-verified` y las firmas del bloque E.
- **Un check run con anotaciones.** Necesita el permiso de escribir `checks`.

## Consecuencias

- El mantenedor abre el job para ver el resultado, y el artefacto para leer la evidencia entera.
- El artefacto se guarda solo mientras GitHub lo guarde. Guardar la evidencia más tiempo es el
  almacén de evidencias de la arquitectura, que A4 no construye.
- Ningún job de este repositorio que ejecute el código de un cambio puede escribir en él.
