"""The digest of a held-out example and the text of each example of a contract (ADR-0014).

The digest of a held-out example is that of the canonical form (ADR-0062) of its salt, in lowercase
hexadecimal, and its text as approved, the block of the example in the contract as it is written.
The salt, 16 bytes from the randomness of the system and a new one for each example, keeps a short
example from being found by trying candidates against its digest, as the salted hashes of RFC 9901
do. The strict reader refuses anchors, aliases, tags and merge keys, so the text of an example reads
the same alone as inside its contract.
"""

from dokime.core.canonical import digest
from dokime.core.reading import read

SALT_BYTES = 16


def held_out_digest(salt: bytes, text: str) -> str:
    """The digest of a held-out example: that of its salt and its text as approved."""
    if len(salt) != SALT_BYTES:
        raise ValueError(f"the salt of a held-out digest is {SALT_BYTES} bytes, not {len(salt)}")
    return digest({"salt": salt.hex(), "text": text})


def example_texts(text: str) -> dict[str, str]:
    """The text of each example of a contract, by its id, as it is written in the file.

    The text of an example runs from the line of its item to the line before the next item or the
    next field of the contract, without the empty lines and the comments that end it.
    """
    reading = read(text)
    root = reading.value
    if not isinstance(root, dict):
        return {}
    examples = root.get("examples")
    if not isinstance(examples, list):
        return {}
    lines = text.splitlines(keepends=True)
    starts = sorted(
        line
        for path, line in reading.lines.items()
        if len(path) == 1 or (len(path) == 2 and path[0] in root)
    )
    texts: dict[str, str] = {}
    for index, item in enumerate(examples):
        if not isinstance(item, dict) or not isinstance(item.get("id"), str):
            continue
        first = reading.lines[("examples", index)]
        after = next((line for line in starts if line > first), len(lines) + 1)
        block = lines[first - 1 : after - 1]
        while block and (not block[-1].strip() or block[-1].lstrip().startswith("#")):
            block.pop()
        texts[str(item["id"])] = "".join(block)
    return texts
