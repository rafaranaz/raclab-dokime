# SDD-EARS: CORPUS-096 CORPUS-097
from pathlib import Path

import pytest

from tests.corpus.data_home import IDENTITY, check_no_identity

SEEN: list[Path] = []


def test_a_directory_without_an_identity_passes(tmp_path: Path) -> None:
    (tmp_path / "containers").mkdir()
    check_no_identity(tmp_path)


def test_a_directory_with_an_identity_fails_naming_the_file(tmp_path: Path) -> None:
    (tmp_path / IDENTITY).parent.mkdir()
    (tmp_path / IDENTITY).write_bytes(b"age-encryption.org/v1")
    with pytest.raises(AssertionError) as failed:
        check_no_identity(tmp_path)
    assert str(tmp_path / IDENTITY) in str(failed.value)


def test_the_data_home_of_a_session_starts_empty(data_home: Path) -> None:
    SEEN.append(data_home)
    assert not (data_home / IDENTITY).exists()


def test_every_test_of_a_session_gets_the_same_data_home(data_home: Path) -> None:
    assert [data_home] == SEEN
