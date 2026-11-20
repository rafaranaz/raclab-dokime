# SDD-EARS: INTERFACES-185
from collections.abc import Iterable, Mapping
from pathlib import Path

import pytest

from dokime.core.repository import FileVersion
from dokime.verify import published as verify_published
from tests.interfaces.seals import contract, example, opened, place, seal
from tests.sandbox.engines import require


def test_the_seal_tells_what_was_published_with_the_function_of_verify(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    require("git")
    calls: list[tuple[list[str], int]] = []

    def spy(
        items: Iterable[Mapping[str, object]], versions: Iterable[FileVersion]
    ) -> frozenset[str]:
        given, read = list(items), list(versions)
        calls.append(([str(i.get("id")) for i in given], len(read)))
        return verify_published.published(given, read)

    monkeypatch.setattr("dokime.interfaces.seal_command.published", spy)
    where = place(tmp_path, history=(contract(example("E-a1", "c1", 1)),))
    assert seal(where) == 0
    ((ids, versions),) = calls
    assert ids == ["E-a1", "E-a2", "E-b1", "E-c1", "E-c2"]
    assert versions == 1
    assert opened(where).kept_visible == ("E-a1",)
