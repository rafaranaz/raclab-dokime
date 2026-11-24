"""The fixtures that the tests of the corpus share."""

from collections.abc import Iterator
from pathlib import Path

import pytest

from tests.corpus.data_home import check_no_identity, storage_size


@pytest.fixture(scope="session")
def data_home(tmp_path_factory: pytest.TempPathFactory) -> Iterator[Path]:
    """One empty `XDG_DATA_HOME` for every audit of the session, checked to hold no identity when
    the session starts and when it ends (CORPUS-096, CORPUS-097)."""
    directory = tmp_path_factory.mktemp("data-home")
    check_no_identity(directory)
    yield directory
    check_no_identity(directory)
    print(f"\n[corpus] the storage of podman of the session takes {storage_size(directory)}")
