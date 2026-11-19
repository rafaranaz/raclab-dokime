# SDD-EARS: PLATFORM-110 PLATFORM-111 PLATFORM-112 PLATFORM-114
import os
import subprocess
import sys
import termios
import threading
from pathlib import Path

import pytest

from dokime.core.repository import RefusalError
from dokime.platform.sealed_store import read_passphrase


def test_a_descriptor_gives_the_passphrase_up_to_its_first_newline() -> None:
    read, write = os.pipe()
    os.write(write, b"the passphrase\nwhat follows\n")
    os.close(write)
    try:
        assert read_passphrase(read) == "the passphrase"
    finally:
        os.close(read)


def test_a_descriptor_without_a_newline_gives_all_it_holds() -> None:
    read, write = os.pipe()
    os.write(write, b"no newline")
    os.close(write)
    try:
        assert read_passphrase(read) == "no newline"
    finally:
        os.close(read)


def test_the_terminal_gives_the_passphrase_without_echo(tmp_path: Path) -> None:
    main, side = os.openpty()
    name = os.ttyname(side)
    seen: list[bytes] = []

    def type_it() -> None:
        said = b""
        while b":" not in said:
            said += os.read(main, 1024)
        seen.append(said)
        assert not termios.tcgetattr(side)[3] & termios.ECHO
        os.write(main, b"typed secret\n")

    typist = threading.Thread(target=type_it, daemon=True)
    typist.start()
    try:
        assert read_passphrase(None, terminal=name) == "typed secret"
    finally:
        typist.join(timeout=10)
    assert termios.tcgetattr(side)[3] & termios.ECHO
    os.set_blocking(main, False)
    try:
        echoed = os.read(main, 1024)
    except BlockingIOError:
        echoed = b""
    assert b"typed secret" not in echoed
    assert seen
    os.close(main)
    os.close(side)


def test_without_a_descriptor_nor_a_terminal_it_is_refused(tmp_path: Path) -> None:
    with pytest.raises(RefusalError) as refused:
        read_passphrase(None, terminal=str(tmp_path / "no-terminal"))
    assert refused.value.finding.code == "no-passphrase-source"


def test_a_process_without_a_terminal_does_not_read_its_standard_input() -> None:
    program = (
        "from dokime.core.repository import RefusalError\n"
        "from dokime.platform.sealed_store import read_passphrase\n"
        "try:\n"
        "    print(read_passphrase(None))\n"
        "except RefusalError as refused:\n"
        "    print(refused.finding.code)\n"
    )
    done = subprocess.run(
        [sys.executable, "-c", program],
        input="from the standard input\n",
        capture_output=True,
        text=True,
        check=False,
        start_new_session=True,
        env={**os.environ, "DOKIME_PASSPHRASE": "from the environment"},
        timeout=60,
    )
    assert done.stdout == "no-passphrase-source\n", done.stderr


@pytest.mark.parametrize("raw", [b"\xff\xfe\n", b"caf\xe9\n"])
def test_a_passphrase_that_is_not_utf8_is_refused(raw: bytes) -> None:
    read, write = os.pipe()
    os.write(write, raw)
    os.close(write)
    try:
        with pytest.raises(RefusalError) as refused:
            read_passphrase(read)
    finally:
        os.close(read)
    assert refused.value.finding.code == "unreadable-passphrase"
