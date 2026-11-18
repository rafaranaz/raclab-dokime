<!-- translation-of: 0072-the-sealed-store-is-encrypted-with-age-for-a-list-of-recipients.md sha256:ce24498e9765e536 -->
# ADR-0072 · El almacén sellado se cifra con age para una lista de destinatarios

**Estado:** aceptada

## Contexto

El bloque B guarda los ejemplos reservados de un contrato en un almacén sellado: contenido reservado
"cifrado para una lista de destinatarios", un fichero cifrado en el repositorio
([arquitectura](../architecture/02-modules.es.md)). El roadmap dejó para antes de B1 la herramienta
que lo cifra. La lista de destinatarios tiene al menos dos: el mantenedor y un segundo destinatario
que guarda una copia, para que perder una clave no pierda los ejemplos reservados. dokime tiene hoy
una sola dependencia en tiempo de ejecución, `pyyaml`.

La revisión estratégica al cerrar el bloque A comparó las opciones; el mantenedor aprobó esta
recomendación. La sesión que revisa el trabajo la investigó primero; la decisión es del mantenedor.

## Decisión

**La regla.** El contenido reservado se cifra con un formato publicado y una implementación
consolidada de él, nunca con un formato propio, para una lista de destinatarios, cualquiera de los
cuales puede descifrarlo.

**El mecanismo en el bloque B, en uso atendido.**

- **El formato es age** (`age-encryption.org/v1`), con los destinatarios dados por sus claves
  públicas.
- **La implementación es `pyrage`**, una dependencia de Python fijada en `uv.lock` con sus
  huellas, usada solo dentro del adaptador del almacén sellado, que la
  [tabla de módulos](../architecture/02-modules.es.md) pone en `platform`.
- **Cualquier destinatario descifra un lote sellado solo**; añadir o quitar un destinatario es
  volver a cifrar el lote.

## Base

Comprobado el 2026-11-18:

- [pyrage](https://pypi.org/project/pyrage/) 1.4.0, publicada el 23 de agosto de 2026, después de
  las 1.2.1 a 1.3.0 entre septiembre de 2024 y junio de 2025; su
  [repositorio](https://github.com/woodruffw/pyrage) no está archivado y tuvo commits hasta el 13 de
  octubre de 2026. Es el repositorio de una sola persona. Sus ruedas son abi3 para Python 3.10 en
  adelante, para Linux x86_64 y aarch64, macOS y Windows, y la rueda de Linux x86_64 lleva una
  atestación de procedencia en PyPI, publicada desde su workflow `release.yml`.
- Su README cifra para varios destinatarios en una llamada: `encrypt(data, [carol, dave,
  alice.to_public()])`, con destinatarios x25519 y SSH.
- El formato tiene dos implementaciones independientes, las dos con versiones recientes:
  [age](https://github.com/FiloSottile/age) v1.3.2 (29 de agosto de 2026), en Go, y
  [rage](https://github.com/str4d/rage) v0.12.1 (14 de julio de 2026), en Rust, que es la que enlaza
  pyrage.
- [SOPS](https://getsops.io/docs/) v3.13.3 (julio de 2026) admite los formatos "YAML, JSON, ENV, INI
  and BINARY".

Razonamiento, sin prueba: que un formato con especificación y dos implementaciones mantiene legibles
los lotes sellados si pyrage deja de mantenerse, porque los binarios `age` y `rage` descifran los
mismos ficheros. La prueba es descifrar con el binario `age` un lote escrito por pyrage, en B1.

## Alternativas consideradas

- **El binario `age` tras un adaptador propio.** Sin dependencia de Python, pero con un programa más
  que fijar e instalar, y un subproceso por cada lote.
- **SOPS.** Cifra ficheros para age, PGP y los servicios de claves de las nubes, y cambia los
  destinatarios con `sops updatekeys`. Es un binario más y su alcance son los secretos de
  configuración, que dokime no necesita. La investigación sostenía que deja en claro la estructura
  del fichero, lo que enseñaría cuántos ejemplos se reservan; eso no se encontró en su
  documentación, que admite un formato BINARY.
- **Un sobre propio sobre `cryptography`.** Un formato que nadie más lee ni revisa.
- **git-crypt.** No se examinó.

## Consecuencias

- dokime gana una segunda dependencia en tiempo de ejecución, compilada, con ruedas para las
  plataformas de arriba; una plataforma sin rueda la compila desde el código con Rust.
- age no rellena el contenido: la
  [especificación](https://github.com/C2SP/C2SP/blob/main/age.md) parte la carga en trozos de
  64 KiB, cuyo último trozo "MAY be shorter than 64 KiB", cada uno cifrado con ChaCha20-Poly1305,
  que añade una etiqueta de tamaño fijo. Así que el tamaño de un fichero sellado deja ver
  aproximadamente cuánto contenido reservado hay. Saber cuántos ejemplos hay reservados no ayuda a
  hacer trampa, pero es el mismo tipo de fuga contra el que se sopesa arriba la alternativa de SOPS.
- El mantenimiento de pyrage depende de una persona. Si se detiene, el adaptador puede llamar al
  binario `age` sin cambiar los ficheros.
- Solo `platform` importa `pyrage`; un contrato de importación de `lint-imports` lo dice cuando
  se construya el adaptador.
- Dónde viven las claves privadas se decide aparte, en la ADR siguiente.
