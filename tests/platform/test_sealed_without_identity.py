# SDD-EARS: PLATFORM-096
from pathlib import Path

import pytest

from dokime.core.repository import RefusalError
from tests.platform.test_sealed_store import SECRET, made


def test_a_content_sealed_without_an_identity_opens_with_a_recipient(tmp_path: Path) -> None:
    from dokime.platform.sealed_store import seal_for

    maintainer, store = made(tmp_path, "maintainer")
    sealed = seal_for(SECRET, [maintainer])
    assert sealed.startswith(b"age-encryption.org/v1\n")
    assert store.open(sealed) == SECRET


def test_sealing_without_an_identity_refuses_bad_recipients() -> None:
    from dokime.platform.sealed_store import seal_for

    with pytest.raises(RefusalError) as refused:
        seal_for(SECRET, ["age1zzz"])
    assert refused.value.finding.code == "bad-recipient"
