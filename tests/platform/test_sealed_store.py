# SDD-EARS: PLATFORM-090 PLATFORM-091 PLATFORM-092 PLATFORM-093 PLATFORM-094 PLATFORM-095
import os
import pty
import shutil
import subprocess
from pathlib import Path

import pytest

from dokime.core.repository import RefusalError
from dokime.platform.sealed_store import AgeSealedStore, create_identity, load_identity

SECRET = b'{"held_out": ["the content of a held-out example"]}'


def made(tmp_path: Path, name: str) -> tuple[str, AgeSealedStore]:
    """A new identity in a temporary directory: its recipient and its store."""
    path = tmp_path / name / "identity.age"
    recipient = create_identity(path, f"passphrase of {name}")
    store, _ = load_identity(path, f"passphrase of {name}")
    return recipient, store


def test_any_one_of_the_recipients_opens_what_is_sealed(tmp_path: Path) -> None:
    maintainer, first = made(tmp_path, "maintainer")
    second_recipient, second = made(tmp_path, "second")
    sealed = first.seal(SECRET, [maintainer, second_recipient])
    assert sealed.startswith(b"age-encryption.org/v1\n")
    assert SECRET not in sealed
    assert first.open(sealed) == SECRET
    assert second.open(sealed) == SECRET


@pytest.mark.parametrize("recipients", [[], ["age1zzz"], ["ssh-ed25519 AAAA"]])
def test_a_list_without_valid_recipients_is_refused(tmp_path: Path, recipients: list[str]) -> None:
    _, store = made(tmp_path, "maintainer")
    with pytest.raises(RefusalError) as refused:
        store.seal(SECRET, recipients)
    assert refused.value.finding.code == "bad-recipient"


def test_opening_writes_no_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    maintainer, store = made(tmp_path, "maintainer")
    sealed = store.seal(SECRET, [maintainer])
    work = tmp_path / "work"
    work.mkdir()
    monkeypatch.chdir(work)
    monkeypatch.setenv("TMPDIR", str(work))
    before = sorted(tmp_path.rglob("*"))
    assert store.open(sealed) == SECRET
    assert sorted(tmp_path.rglob("*")) == before


def test_an_identity_that_is_not_a_recipient_is_refused(tmp_path: Path) -> None:
    maintainer, store = made(tmp_path, "maintainer")
    _, stranger = made(tmp_path, "stranger")
    sealed = store.seal(SECRET, [maintainer])
    with pytest.raises(RefusalError) as refused:
        stranger.open(sealed)
    assert refused.value.finding.code == "not-a-recipient"


@pytest.mark.parametrize("sealed", [b"", b"not age at all", b"age-encryption.org/v1\nbroken"])
def test_bytes_that_are_not_an_age_file_are_refused(tmp_path: Path, sealed: bytes) -> None:
    _, store = made(tmp_path, "maintainer")
    with pytest.raises(RefusalError) as refused:
        store.open(sealed)
    assert refused.value.finding.code == "unreadable-batch"


def test_the_binary_age_opens_a_batch_with_the_identity_and_its_passphrase(
    tmp_path: Path,
) -> None:
    age = shutil.which("age")
    if age is None:
        pytest.skip("the binary age is not installed")
    path = tmp_path / "identity.age"
    recipient = create_identity(path, "a passphrase for age")
    store, _ = load_identity(path, "a passphrase for age")
    batch = tmp_path / "sealed.age"
    batch.write_bytes(store.seal(SECRET, [recipient]))
    out = tmp_path / "opened"
    pid, terminal = pty.fork()
    if pid == 0:  # the child, whose terminal is the pty where the passphrase is typed
        os.execv(  # noqa: S606 - the binary age, found on the path, run in the pty
            age, [age, "--decrypt", "--identity", str(path), "--output", str(out), str(batch)]
        )
    said = b""
    while b"passphrase" not in said.lower():
        said += os.read(terminal, 1024)
    os.write(terminal, b"a passphrase for age\n")
    try:
        while os.read(terminal, 1024):
            pass
    except OSError:
        pass
    _, status = os.waitpid(pid, 0)
    assert os.waitstatus_to_exitcode(status) == 0
    assert out.read_bytes() == SECRET
    assert subprocess.run([age, "--version"], capture_output=True, check=False).returncode == 0
