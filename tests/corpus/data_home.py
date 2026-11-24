"""The `XDG_DATA_HOME` that the audits of a session of pytest share, and the check that it holds no
identity, where `audit` would find one by default."""

import shutil
import subprocess
from pathlib import Path

IDENTITY = Path("dokime") / "identity.age"


def check_no_identity(directory: Path) -> None:
    """Fail when the directory holds the identity that `audit` looks for by default."""
    found = directory / IDENTITY
    if found.exists() or found.is_symlink():
        raise AssertionError(f"the data home of the corpus holds an identity: {found}")


def storage_size(directory: Path) -> str:
    """The space that the storage of podman takes under a data home, as `du` gives it, read inside
    the user namespace of podman, whose files the user cannot all read."""
    storage = directory / "containers"
    if not storage.exists() or shutil.which("podman") is None:
        return "nothing"
    done = subprocess.run(
        ["podman", "unshare", "du", "-sh", str(storage)],
        capture_output=True,
        text=True,
        check=False,
    )
    return done.stdout.split("\t", 1)[0].strip() or "unknown"
