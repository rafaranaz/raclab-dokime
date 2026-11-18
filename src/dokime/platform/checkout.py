"""The commit of the checkout of git that holds a directory, such as that of the harness.

The evidence names the harness by its version and its commit (ADR-0068). A commit names the code
only when the checkout has no change: none to the files git follows, and no file it neither
follows nor ignores. git runs with the environment of the adapter, which reads no configuration
but that of the checkout, and with the monitor of the file system and the hooks turned off, so that
no program the configuration names runs.
"""

import shutil
import subprocess
from pathlib import Path

from dokime.core.repository import CommitName
from dokime.platform.git import _environment

_QUIET = ("-c", "core.fsmonitor=false", "-c", "core.hooksPath=/dev/null")


def checkout_commit(directory: Path, *, git: str = "git") -> CommitName | None:
    """The commit of `HEAD` of the checkout that holds the directory, when it names its code."""
    found = shutil.which(git)
    if found is None:
        return None

    def ask(*args: str) -> str | None:
        done = subprocess.run(
            [found, *_QUIET, "-C", str(directory), *args],
            capture_output=True,
            text=True,
            env=_environment({}),
            check=False,
        )
        return done.stdout.strip() if done.returncode == 0 else None

    head = ask("rev-parse", "--verify", "--quiet", "HEAD^{commit}")
    if not head:
        return None
    changes = ask("status", "--porcelain", "--untracked-files=normal", "--ignore-submodules=none")
    if changes is None or changes:
        return None
    return CommitName(head)
