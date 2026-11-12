<!-- translation-of: 0042-memory-persists-on-local-disk-or-in-its-own-git-repository.md sha256:0ae8f9367c68974f -->
# ADR-0042 · La memoria persiste en disco local o en su propio repositorio git

**Estado:** aceptada

## Contexto

El [ADR-0027](0027-memory-has-one-layout-and-three-scopes.es.md) dice que la memoria tiene una
disposición y dos almacenamientos, "a local directory without git for a single developer, or the
repository for a team". La decisión que recogía era "la misma estructura en local y en git": la
memoria es un almacén propio, guardado como un directorio sin más o como un repositorio git.
Escrito como "the repository", se leyó después como el repositorio del proyecto verificado: el
documento de datos puso la memoria en `.dokime/` dentro de ese proyecto, y el
[ADR-0041](0041-the-environment-of-a-verified-project-is-a-dockerfile.es.md) puso ahí el pack.
Este registro fija las dos formas en que persiste la memoria y quién usa cada una, para que no se
pueda volver a leer así.

## Decisión

- **La memoria es un almacén propio.** Nunca está dentro del repositorio del proyecto verificado,
  y ese repositorio no contiene nada del arnés.
- **Dos modos de persistencia, que elige quien usa el arnés:**

| Modo | Dónde está la memoria | Quién lo usa |
|---|---|---|
| Disco local | Un directorio en la máquina, sin git | Una persona que usa el arnés sola y elige guardar la memoria en local |
| Repositorio git | Un repositorio git propio, aparte del repositorio del proyecto verificado | Una persona, o un equipo de más de una, que eligen git para poder compartir la memoria del proyecto |

- **La disposición es la misma en los dos modos**, la del ADR-0027.
- **Lo que contiene la memoria** es lo que contienen los tres ámbitos del ADR-0027: del proyecto,
  el glosario, las decisiones, la política, el pack, el flujo y la lista de firmantes admitidos;
  de cada cambio, su contrato, sus ejemplos, sus aclaraciones, su aprobación y su lote sellado; de
  la persona, el estado del trabajo en curso y las propuestas sin aprobar.
- **El ámbito de la persona se queda en la máquina en los dos modos.** No se sube al repositorio
  git de la memoria.
- **El pack** de un proyecto verificado está en su memoria, en el ámbito del proyecto, o es un
  fichero que se le da a la orden. Esto sustituye al sitio que le daba el ADR-0041.

## Base

Una decisión del mantenedor, tomada antes de que se escribieran los primeros registros y
reafirmada ahora. La redacción anterior está en la lista de decisiones acordadas: "la misma
estructura en local y en git". La conversación en la que se tomó no está disponible, así que sus
palabras exactas no se pueden citar.

Razonamiento: el proyecto verificado puede ser de otro, como lo son los repositorios del corpus,
y el arnés no los cambia; y una memoria que se comparte entre proyectos de la misma persona o del
mismo equipo necesita un sitio que no sea ninguno de ellos. De memoria, sin comprobar: las
herramientas que guardan especificaciones suelen poner sus ficheros dentro del repositorio del
proyecto, cosa que esta decisión no hace. Sin prueba.

## Alternativas consideradas

- **La memoria dentro del repositorio del proyecto verificado.** Lo que los registros decían por
  error. Mete ficheros del arnés en un repositorio que puede no ser nuestro, y hace público lo que
  una persona o un equipo pueden querer privado.
- **Solo lo que se firma dentro del proyecto, y el resto fuera.** Parte una disposición en dos
  sitios, y el ADR-0027 ya cuenta el contrato y el pack como memoria.

## Consecuencias

- A una auditoría que corre en un pipeline hay que darle la memoria: una copia de su repositorio
  git, o los ficheros del cambio.
- La memoria de un proyecto público puede ser privada. La evidencia cita entonces por su huella un
  contrato que no todo el mundo puede leer.
- Un cambio vive en dos sitios que van juntos: la rama en el repositorio del proyecto y el
  directorio del cambio en la memoria, unidos por el id de la historia.
- En disco local, las aprobaciones no tienen rastro independiente, como ya dice el ADR-0027.
