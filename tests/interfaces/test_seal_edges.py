# SDD-EARS: INTERFACES-161 INTERFACES-164 INTERFACES-165 INTERFACES-169 INTERFACES-173
import os
import pty
import sys
from pathlib import Path

import pytest

from dokime.core.layout import sealed_path
from dokime.platform.randomness import random_bytes
from tests.interfaces.seals import STORY, contract, example, git, opened, place, seal
from tests.sandbox.engines import require


@pytest.fixture(autouse=True)
def needs_git() -> None:
    require("git")


def test_a_contract_without_a_case_of_two_examples_is_not_sealed(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    where = place(tmp_path)
    where.approved.write_text(contract(example("E-a1", "c1", 1) + example("E-b1", "c2", 2)))
    assert seal(where) == 2
    said = capsys.readouterr()
    assert "nothing-to-hold-out" in said.out
    assert "c1" in said.out
    assert "single-example" in said.out
    assert not (where.project / str(sealed_path(STORY))).exists()


def test_a_contract_that_cannot_be_read_is_refused(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    where = place(tmp_path)
    where.approved.write_bytes(b"\xff\xfe not text")
    assert seal(where) == 2
    assert "unreadable-file" in capsys.readouterr().out


@pytest.mark.parametrize(
    ("recipients", "code"),
    [(b"age1zzz\n", "bad-recipient"), (b"\xff\xfe\n", "unreadable-file")],
)
def test_recipients_of_head_that_do_not_read_are_refused(
    tmp_path: Path, recipients: bytes, code: str, capsys: pytest.CaptureFixture[str]
) -> None:
    where = place(tmp_path)
    (where.project / ".dokime" / "recipients.txt").write_bytes(recipients)
    git(where.project, "add", "--all")
    git(where.project, "commit", "--quiet", "--message", "other recipients")
    assert seal(where) == 2
    assert code in capsys.readouterr().out


def test_a_contract_without_a_final_newline_is_sealed(tmp_path: Path) -> None:
    where = place(tmp_path)
    examples = contract().split("examples:\n", 1)[1] + example("E-z1", "cz", 9)
    where.approved.write_text(contract(examples).rstrip("\n"))
    assert seal(where) == 0
    assert opened(where).examples


def test_a_version_of_the_history_without_a_list_of_examples_is_read_as_none(
    tmp_path: Path,
) -> None:
    where = place(tmp_path, history=("format: 1\nexamples: none\n",))
    assert seal(where) == 0
    assert opened(where).kept_visible == ()


def test_the_id_of_the_canary_is_never_one_of_the_contract(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    drawn = iter([bytes.fromhex("a1a1"), bytes.fromhex("c0de")])

    def colliding(count: int) -> bytes:
        return next(drawn) if count == 2 else random_bytes(count)

    monkeypatch.setattr("dokime.interfaces.seal_command.random_bytes", colliding)
    where = place(tmp_path)
    where.approved.write_text(contract().replace("E-a1", "E-a1a1"))
    assert seal(where) == 0
    assert opened(where).canary.id == "E-c0de"


def test_the_terminal_gives_the_confirmation(tmp_path: Path) -> None:
    where = place(tmp_path)
    arguments = [
        "contract",
        "seal",
        "--story",
        STORY,
        "--contract",
        str(where.approved),
        "--out",
        str(where.out),
        "--project",
        str(where.project),
    ]
    pid, terminal = pty.fork()
    if pid == 0:  # the child, whose terminal is the pty where the answer is typed
        os.execv(  # noqa: S606 - this Python, running the command in the pty
            sys.executable,
            [
                sys.executable,
                "-c",
                f"from dokime.interfaces.cli import main; exit(main({arguments!r}))",
            ],
        )
    said = b""
    while b"[y/N]" not in said:
        said += os.read(terminal, 1024)
    os.write(terminal, b"y\n")
    try:
        while os.read(terminal, 1024):
            pass
    except OSError:
        pass
    _, status = os.waitpid(pid, 0)
    assert os.waitstatus_to_exitcode(status) == 0
    assert where.recipient.encode() in said
    assert opened(where).examples
