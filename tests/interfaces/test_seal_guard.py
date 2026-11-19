# SDD-EARS: INTERFACES-174
from pathlib import Path

import pytest

from dokime.core.layout import contract_path, sealed_path
from dokime.interfaces import seal_command
from tests.interfaces.seals import STORY, example, place, seal
from tests.sandbox.engines import require


def test_a_contract_written_without_a_visible_example_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    require("git")
    real = seal_command._visible_text

    def losing(text: str, sealed: tuple[object, ...]) -> str:
        return real(text, sealed).replace(example("E-b1", "c2", 3), "", 1)  # type: ignore[arg-type]

    monkeypatch.setattr(seal_command, "_visible_text", losing)
    where = place(tmp_path)
    assert seal(where) == 2
    assert "split-not-written" in capsys.readouterr().out
    assert not (where.project / str(sealed_path(STORY))).exists()
    assert not (where.project / str(contract_path(STORY))).exists()
