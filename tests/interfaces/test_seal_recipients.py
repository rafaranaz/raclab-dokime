# SDD-EARS: INTERFACES-164 INTERFACES-165 INTERFACES-166
import os
import subprocess
import sys
from pathlib import Path

import pytest

from dokime.core.layout import sealed_path
from tests.interfaces.seals import STORY, opened, place, seal
from tests.sandbox.engines import require


@pytest.fixture(autouse=True)
def needs_git() -> None:
    require("git")


def test_the_batch_is_sealed_for_the_recipients_of_head(tmp_path: Path) -> None:
    where = place(tmp_path)
    assert seal(where) == 0
    assert opened(where).story == STORY


def test_each_recipient_is_shown_before_the_answer(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    where = place(tmp_path)
    assert seal(where) == 0
    assert where.recipient in capsys.readouterr().err


@pytest.mark.parametrize("answer", ["n\n", "\n", "no\n", "maybe\n", ""])
def test_any_answer_but_yes_is_refused(
    tmp_path: Path, answer: str, capsys: pytest.CaptureFixture[str]
) -> None:
    where = place(tmp_path)
    assert seal(where, answer) == 2
    assert "recipients-not-confirmed" in capsys.readouterr().out
    assert not (where.project / str(sealed_path(STORY))).exists()


@pytest.mark.parametrize("answer", ["y\n", "yes\n", "Y\n", "YES\n"])
def test_yes_seals(tmp_path: Path, answer: str) -> None:
    assert seal(place(tmp_path), answer) == 0


def test_without_a_descriptor_nor_a_terminal_it_is_refused(tmp_path: Path) -> None:
    where = place(tmp_path)
    arguments = [
        "contract",
        "seal",
        "--story",
        "add-one",
        "--contract",
        str(where.approved),
        "--out",
        str(where.out),
        "--project",
        str(where.project),
    ]
    program = f"import sys\nfrom dokime.interfaces.cli import main\nsys.exit(main({arguments!r}))\n"
    done = subprocess.run(
        [sys.executable, "-c", program],
        input="y\n",
        capture_output=True,
        text=True,
        check=False,
        start_new_session=True,
        env=dict(os.environ),
        timeout=120,
    )
    assert done.returncode == 2, done.stderr
    assert "no-confirmation-source" in done.stdout
    assert not (where.project / str(sealed_path(STORY))).exists()
