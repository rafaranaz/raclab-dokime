# SDD-EARS: INTERFACES-175 INTERFACES-176 INTERFACES-180
import os
from pathlib import Path

import pytest

from dokime.core.repository import RefusalError
from dokime.interfaces.audit_command import IdentityStore, key_from
from dokime.interfaces.cli import main
from dokime.platform.sealed_store import create_identity, seal_for

PASSPHRASE = "a passphrase for the tests"  # noqa: S105 - of a test identity, made and dropped here


def audited(tmp_path: Path, identity: Path, capsys: pytest.CaptureFixture[str]) -> tuple[int, str]:
    project = tmp_path / "project"
    project.mkdir(exist_ok=True)
    patch = tmp_path / "change.patch"
    patch.write_bytes(b"")
    code = main(
        [
            "audit",
            "--base",
            "a" * 40,
            "--patch",
            str(patch),
            "--story",
            "a-story",
            "--out",
            str(tmp_path / "out"),
            "--project",
            str(project),
            "--identity",
            str(identity),
        ]
    )
    return code, capsys.readouterr().out


def test_an_identity_inside_the_tree_is_refused(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    inside = tmp_path / "project" / "identity.age"
    inside.parent.mkdir()
    create_identity(inside, PASSPHRASE)
    code, said = audited(tmp_path, inside, capsys)
    assert code == 2
    assert "inside-the-tree" in said


def test_an_identity_that_does_not_exist_is_refused(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code, said = audited(tmp_path, tmp_path / "keys" / "none.age", capsys)
    assert code == 2
    assert "no-identity" in said


def test_without_identity_the_default_path_is_the_key_when_a_file_is_there(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    environ = {"XDG_DATA_HOME": str(tmp_path / "data")}
    assert key_from(None, project, environ, None) is None
    create_identity(tmp_path / "data" / "dokime" / "identity.age", PASSPHRASE)
    key = key_from(None, project, environ, None)
    assert isinstance(key, IdentityStore)
    assert key.identity == tmp_path / "data" / "dokime" / "identity.age"


def test_without_a_home_there_is_no_key(tmp_path: Path) -> None:
    assert key_from(None, tmp_path / "project", {}, None) is None


def test_the_passphrase_is_asked_when_the_batch_is_first_opened_and_once(tmp_path: Path) -> None:
    identity = tmp_path / "keys" / "identity.age"
    recipient = create_identity(identity, PASSPHRASE)
    sealed = seal_for(b"the batch", [recipient])
    read, write = os.pipe()
    try:
        store = key_from(identity, tmp_path / "project", {}, read)
        assert store is not None
        os.write(write, f"{PASSPHRASE}\n".encode())
        os.close(write)
        assert store.open(sealed) == b"the batch"
        assert store.open(sealed) == b"the batch"
    finally:
        os.close(read)


def test_a_wrong_passphrase_is_refused(tmp_path: Path) -> None:
    identity = tmp_path / "keys" / "identity.age"
    recipient = create_identity(identity, PASSPHRASE)
    read, write = os.pipe()
    os.write(write, b"not the passphrase\n")
    os.close(write)
    try:
        store = key_from(identity, tmp_path / "project", {}, read)
        assert store is not None
        with pytest.raises(RefusalError) as refused:
            store.open(seal_for(b"x", [recipient]))
        assert refused.value.finding.code == "wrong-passphrase"
    finally:
        os.close(read)


def test_an_identity_open_to_others_is_opened_with_a_warning(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    identity = tmp_path / "keys" / "identity.age"
    recipient = create_identity(identity, PASSPHRASE)
    identity.chmod(0o644)
    read, write = os.pipe()
    os.write(write, f"{PASSPHRASE}\n".encode())
    os.close(write)
    try:
        store = key_from(identity, tmp_path / "project", {}, read)
        assert store is not None
        assert store.open(seal_for(b"x", [recipient])) == b"x"
    finally:
        os.close(read)
    assert "dokime audit:" in capsys.readouterr().err


def test_the_store_of_an_audit_seals_nothing(tmp_path: Path) -> None:
    with pytest.raises(NotImplementedError):
        IdentityStore(tmp_path / "identity.age", None).seal(b"x", [])
