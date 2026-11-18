<!-- translation-of: 0068-the-harness-is-named-by-its-version-and-its-commit.md sha256:3fe694e77edd22ee -->
# ADR-0068 · El arnés se nombra por su versión y su commit

**Estado:** propuesta

## Contexto

La evidencia registra la versión del arnés que la produjo
([ADR-0064](0064-the-evidence-of-a3-is-an-unsigned-statement-with-a-closed-predicate.es.md)). La
versión es `0.0.0` en `pyproject.toml`, la misma en todos los commits, así que dos ejecuciones de
código distinto dicen lo mismo. A4 acaba con la versión 0.1, y el roadmap dejó para antes de A4 cómo
se versiona y se publica el arnés. En A4 el arnés audita las pull requests de este repositorio,
ejecutándose desde su propio checkout en CI.

## Decisión

**La regla.** La evidencia nombra sin ambigüedad el código del arnés que la produjo.

**El mecanismo en A4.**

- **La versión se escribe a mano** en `pyproject.toml`, el proyecto `raclab-dokime`. Pasa a `0.1.0`
  cuando A4 se cierre, con la etiqueta `v0.1.0` en ese commit.
- **La evidencia registra también el commit del arnés**, porque todos los commits entre dos
  versiones tienen la misma versión
  ([ADR-0069](0069-the-predicate-v0-2-adds-what-a4-records.es.md)).
- **El arnés no se publica en A4.** El workflow de la auditoría lo ejecuta desde el checkout de este
  repositorio. Se publica, con las atestaciones del índice de paquetes, cuando alguien de fuera de
  este repositorio lo use.

## Base

Comprobado:

- setuptools-scm y hatch-vcs sacan la versión de las etiquetas de git, con
  `dynamic = ["version"]` en `pyproject.toml`
  ([setuptools-scm](https://setuptools-scm.readthedocs.io/en/stable/)).
- PyPI genera atestaciones PEP 740 por defecto para un proyecto que publica desde GitHub Actions con
  Trusted Publishing y `pypa/gh-action-pypi-publish` desde la 1.11
  ([PyPI](https://blog.pypi.org/posts/2024-11-14-pypi-now-supports-digital-attestations/),
  [su documentación](https://docs.pypi.org/attestations/)).

Buscado y no encontrado: si el backend de este repositorio, `uv_build`, toma la versión de las
etiquetas de git.

Razonamiento, sin prueba: que una versión y un commit nombran el código sin ambigüedad, y que una
versión a mano cuesta una línea en cada lanzamiento. La prueba es la evidencia de la primera pull
request de A4, que tiene que nombrar las dos.

## Alternativas consideradas

- **La versión de las etiquetas de git**, con setuptools-scm o hatch-vcs. Necesita otro backend de
  construcción, y cada commit entre dos etiquetas recibe una versión propia, que el commit de la
  evidencia ya da.
- **Publicar la 0.1 en PyPI**, con Trusted Publishing y sus atestaciones. Nadie de fuera de este
  repositorio usa todavía el arnés, y un nombre publicado es difícil de retirar.
- **Solo la versión, sin el commit.** Todos los commits entre dos versiones dirían lo mismo.

## Consecuencias

- Subir la versión es un commit propio en el cierre de un hito que la publica.
- La evidencia lleva un campo más, el commit, que necesita la próxima versión del predicado.
- Un arnés que no se ejecuta desde un checkout de git no tiene commit que registrar; la evidencia
  omite el campo, como omite lo que una ejecución no alcanza.
