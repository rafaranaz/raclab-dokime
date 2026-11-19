# SDD-EARS: PLATFORM-100 PLATFORM-101 PLATFORM-102 PLATFORM-103 PLATFORM-104
import stat
from pathlib import Path

import pytest

from dokime.core.repository import RefusalError
from dokime.core.sealed import read_recipients
from dokime.platform.sealed_store import create_identity, load_identity


def mode(path: Path) -> int:
    return stat.S_IMODE(path.stat().st_mode)


def test_a_new_identity_is_encrypted_and_gives_its_recipient(tmp_path: Path) -> None:
    path = tmp_path / "identity.age"
    recipient = create_identity(path, "a passphrase")
    assert read_recipients(recipient + "\n") == ((recipient,), ())
    data = path.read_bytes()
    assert data.startswith(b"age-encryption.org/v1\n")
    assert b"AGE-SECRET-KEY" not in data
    assert recipient.encode() not in data


def test_the_file_is_0600_and_its_new_directories_0700(tmp_path: Path) -> None:
    path = tmp_path / "data" / "dokime" / "identity.age"
    create_identity(path, "a passphrase")
    assert mode(path) == 0o600
    assert mode(tmp_path / "data") == 0o700
    assert mode(tmp_path / "data" / "dokime") == 0o700


def test_an_existing_file_is_never_replaced(tmp_path: Path) -> None:
    path = tmp_path / "identity.age"
    path.write_text("something of the person\n")
    with pytest.raises(RefusalError) as refused:
        create_identity(path, "a passphrase")
    assert refused.value.finding.code == "identity-exists"
    assert path.read_text() == "something of the person\n"


def test_an_empty_passphrase_is_refused(tmp_path: Path) -> None:
    path = tmp_path / "identity.age"
    with pytest.raises(RefusalError) as refused:
        create_identity(path, "")
    assert refused.value.finding.code == "empty-passphrase"
    assert not path.exists()


def test_a_loaded_identity_opens_what_was_sealed_for_it(tmp_path: Path) -> None:
    path = tmp_path / "identity.age"
    recipient = create_identity(path, "a passphrase")
    store, findings = load_identity(path, "a passphrase")
    assert findings == ()
    assert store.open(store.seal(b"x", [recipient])) == b"x"
