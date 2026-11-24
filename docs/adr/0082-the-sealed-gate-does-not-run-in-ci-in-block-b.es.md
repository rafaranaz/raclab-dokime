<!-- translation-of: 0082-the-sealed-gate-does-not-run-in-ci-in-block-b.md sha256:9f3a9120379902da -->
# ADR-0082 · La puerta sellada no corre en CI en el bloque B

**Estado:** propuesta

## Contexto

La [ADR-0073](0073-the-key-of-the-hold-out-lives-outside-ci-until-b4.es.md) mantiene la clave de los
lotes sellados fuera de CI hasta B4, y deja a una ADR de B4 si la puerta `sealed-examples` corre en
CI. Su candidata es un workflow lanzado por `workflow_run`, que corre con el fichero de la rama por
defecto, con la clave como secreto de un entorno restringido a `main`, aceptada solo si el modelo de
amenazas ([ADR-0010](0010-threat-model.es.md)) acepta el contenedor del sandbox como la única
barrera entre la clave y el código del cambio. En B1 el mantenedor dejó a esa misma ADR cómo llega a
un pull request el resultado de una ejecución sellada: un estado del commit, `dokime/sealed-examples`,
y un comentario; si la clave entrara en CI, la puerta se vería en el resumen de su job, como hace la
[ADR-0070](0070-the-evidence-of-a-pull-request-goes-in-the-summary-of-its-job.es.md) con el resto.

Lo que midió el bloque B: la reserva convierte en 0 los 8 aceptos falsos de los casos que solo ella
caza (B3e), en ejecuciones que el mantenedor lanzó en su máquina, escribiendo la contraseña, y que
registra `tests/corpus/held-out-run.toml`. En CI la puerta no se aplica, «the key is not here».

La puerta ejecuta el código del cambio: construye el árbol del cambio y observa sobre él los
ejemplos reservados, en el sandbox. Un job que tiene la clave y ejecuta ese código deja el segundo
activo de la ADR-0010, el contenido reservado, detrás del contenedor solo; y el código hostil dirigido
contra el propio arnés, T5, queda fuera del alcance de ese modelo de amenazas.

## Decisión

- **La puerta `sealed-examples` no corre en CI en el bloque B.** La clave sigue fuera de CI con el
  mecanismo de la ADR-0073: el mantenedor ejecuta la auditoría sellada en local, antes de fusionar, y
  escribe la contraseña; en CI la puerta sigue sin aplicarse, con el motivo de que la clave no está.
- **No se publica en el pull request nada de una ejecución sellada local**: ni un estado del commit
  ni un comentario. Su evidencia se queda en el directorio `--out` de la ejecución, en la máquina del
  mantenedor; para el corpus, `held-out-run.toml` registra cada ejecución.
- **Esto se decide otra vez antes de que el bloque C necesite la puerta sin una persona**, cuando
  un agente escriba el cambio y no haya nadie para escribir una contraseña.

## Fundamento

Comprobado en lo que publica GitHub. El Security Lab de GitHub da como vulnerabilidad real un
workflow lanzado por `workflow_run` que ejecuta, en un contexto con privilegios, lo que viene de un
pull request ([Preventing pwn requests](https://securitylab.github.com/research/github-actions-preventing-pwn-requests)),
y la documentación de GitHub pide tratar lo que viene de un pull request solo como datos
([securely using pull_request_target](https://docs.github.com/en/enterprise-cloud@latest/actions/reference/security/securely-using-pull_request_target)).
La puerta sellada no puede tratar el cambio como datos: lo ejecuta.

Razonamiento, sobre eso y sobre la ADR-0010: la única barrera sería el contenedor, contra el que la
ADR-0010 no defiende de código dirigido a él (T5); y el valor de la puerta, medido en B3e, no
depende de dónde corra. Sobre el estado y el comentario, también razonamiento: un estado publicado
desde la máquina del mantenedor necesita allí un token con permiso para escribir estados, y diría en
GitHub algo que ninguna ejecución de GitHub comprobó; el registro en el repositorio basta mientras
una sola persona ejecuta la puerta.

## Alternativas consideradas

- **`workflow_run` con la clave como secreto de un entorno restringido a `main`**, la candidata
  de la ADR-0073. Descartada para el bloque B: acepta el contenedor como la única barrera, y la
  ADR-0010 no lo hace.
- **Un estado del commit publicado desde la ejecución local.** Descartada: necesita un token con
  permiso de escritura en la máquina del mantenedor, y muestra como comprobación de GitHub lo que
  solo vio esa máquina.
- **Un comentario en el pull request con la evidencia de la ejecución local.** Descartada por lo
  mismo, y porque la evidencia de la puerta dice qué id reservado falló, algo que el roadmap deja por
  decidir antes de que la evidencia llegue al agente, en el bloque C.

## Consecuencias

- Un pull request no muestra nada de la reserva; quien fusiona tiene que saber que el mantenedor
  ejecutó la auditoría sellada, y el corpus lo guarda en `held-out-run.toml`.
- La reserva depende de una persona y de una máquina. Los lotes del corpus se sellaron para un solo
  destinatario, así que perder esa identidad los pierde, aunque la ADR-0073 pide un segundo
  destinatario.
- El bloque C, en el que un agente escribe el cambio, tiene que decidir esto otra vez antes de
  apoyarse en la puerta.
