# SDD-EARS: PLATFORM-105 PLATFORM-106 PLATFORM-107 PLATFORM-108 PLATFORM-109
import stat
from pathlib import Path

import pytest

from dokime.core.repository import RefusalError
from dokime.core.verdicts import Verdict
from dokime.platform.sealed_store import create_identity, default_identity_path, load_identity


def mode(path: Path) -> int:
    return stat.S_IMODE(path.stat().st_mode)


def test_a_wrong_passphrase_is_refused(tmp_path: Path) -> None:
    path = tmp_path / "identity.age"
    create_identity(path, "a passphrase")
    with pytest.raises(RefusalError) as refused:
        load_identity(path, "another passphrase")
    assert refused.value.finding.code == "wrong-passphrase"


@pytest.mark.parametrize("permissions", [0o640, 0o604, 0o660, 0o644])
def test_an_identity_more_open_than_0600_is_loaded_with_a_finding(
    tmp_path: Path, permissions: int
) -> None:
    path = tmp_path / "identity.age"
    create_identity(path, "a passphrase")
    path.chmod(permissions)
    store, findings = load_identity(path, "a passphrase")
    (finding,) = findings
    assert (finding.code, finding.verdict) == ("open-identity", Verdict.ASK)
    assert oct(permissions)[2:] in finding.message
    assert store is not None


def test_a_missing_identity_is_refused(tmp_path: Path) -> None:
    with pytest.raises(RefusalError) as refused:
        load_identity(tmp_path / "none.age", "a passphrase")
    assert refused.value.finding.code == "no-identity"


def test_the_default_path_is_under_xdg_data_home() -> None:
    environ = {"XDG_DATA_HOME": "/data", "HOME": "/home/p"}
    assert default_identity_path(environ) == Path("/data/dokime/identity.age")


@pytest.mark.parametrize("environ", [{"HOME": "/home/p"}, {"XDG_DATA_HOME": "", "HOME": "/home/p"}])
def test_without_xdg_data_home_the_path_is_under_local_share(environ: dict[str, str]) -> None:
    assert default_identity_path(environ) == Path("/home/p/.local/share/dokime/identity.age")


@pytest.mark.parametrize("keys", [0, 2])
def test_an_identity_without_exactly_one_secret_key_is_refused(tmp_path: Path, keys: int) -> None:
    from pyrage import passphrase, x25519

    text = "# no key here\n" + "".join(f"{x25519.Identity.generate()}\n" for _ in range(keys))
    path = tmp_path / "identity.age"
    path.write_bytes(bytes(passphrase.encrypt(text.encode(), "a passphrase")))
    with pytest.raises(RefusalError) as refused:
        load_identity(path, "a passphrase")
    assert refused.value.finding.code == "bad-identity"
