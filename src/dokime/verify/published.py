"""The examples of a contract already published in the history of its file (ADR-0014).

An example is published when an example of a version of the contract has its id, or its boundary,
target and steps as YAML reads them. The examples of a version are read from its list `examples`
only: the entries of its list `held_out` name held-out examples, they do not publish them. The
command that seals keeps a published example visible, and the gate of the sealed examples checks
with this same function that the batch kept visible exactly those, and that no held-out example was
published since.

These are limits, not guarantees: the content is compared as YAML reads it, so an example published
with a field added or a value spelt otherwise is not recognised; the versions are those that the
history of the file gives, without a rename nor a commit that the start does not reach; a copy of
an example in another file is not looked for; and the gate reads the history up to the base of the
change, so a held-out example published in a commit of the change and taken back in another is not
seen by its audit: where the project merges keeping the commits, by rebase or by a merge commit,
the next audit sees it, and with a squash merge no audit does.
"""

import json
from collections.abc import Iterable, Mapping

from dokime.core.reading import read
from dokime.core.repository import FileVersion

_CONTENT = ("boundary", "target", "steps")


def example_items(text: str) -> tuple[dict[str, object], ...]:
    """The examples of the list `examples` of a contract, as YAML reads them."""
    value = read(text).value
    examples = value.get("examples") if isinstance(value, dict) else None
    if not isinstance(examples, list):
        return ()
    return tuple(dict(item) for item in examples if isinstance(item, dict))


def published(
    items: Iterable[Mapping[str, object]], versions: Iterable[FileVersion]
) -> frozenset[str]:
    """The ids of the examples given that a version has, by id or by content."""
    ids: set[str] = set()
    contents: set[str] = set()
    for version in versions:
        for item in example_items(version.content.decode("utf-8", errors="replace")):
            if isinstance(item.get("id"), str):
                ids.add(str(item["id"]))
            contents.add(_content(item))
    return frozenset(
        str(item["id"])
        for item in items
        if isinstance(item.get("id"), str) and (item["id"] in ids or _content(item) in contents)
    )


def _content(item: Mapping[str, object]) -> str:
    return json.dumps({key: item.get(key) for key in _CONTENT}, sort_keys=True, default=str)
