"""The versions of a file in the history of git (ADR-0014).

To find a held-out example that was once in clear, the audit reads every version of the contract of
a story in the history that its commit reaches. git runs as `checkout_commit` runs it: with the
environment of the adapter, which reads no configuration but that of the checkout, with the hooks
and the monitor of the file system turned off, and with the attributes read from the empty tree, so
that no filter they name changes the bytes read. Renames are not followed: the path of a contract is
that of its story.
"""

import shutil
import subprocess
from pathlib import Path, PurePosixPath

from dokime.core.repository import CommitName, RefusalError
from dokime.platform.git import _EMPTY_TREE, _environment

_QUIET = ("-c", "core.fsmonitor=false", "-c", "core.hooksPath=/dev/null")


def versions(
    directory: Path, start: CommitName, path: PurePosixPath, *, git: str = "git"
) -> tuple[tuple[CommitName, bytes], ...]:
    """Each commit reachable from `start` that changes the path, newest first, with its bytes."""
    found = shutil.which(git)
    if found is None:
        raise RefusalError("unknown-commit", f"git cannot be found as {git!r}")

    def run(*args: str) -> subprocess.CompletedProcess[bytes]:
        return subprocess.run(
            [found, *_QUIET, "-C", str(directory), *args],
            capture_output=True,
            env=_environment({"GIT_ATTR_SOURCE": _EMPTY_TREE}),
            check=False,
        )

    known = run("rev-parse", "--verify", "--quiet", f"{start.text}^{{commit}}")
    if known.returncode != 0:
        raise RefusalError("unknown-commit", f"{start.text} is not a commit of the checkout")
    listed = run("log", "--no-renames", "--format=%H", start.text, "--", str(path))
    found_versions = []
    for line in listed.stdout.decode().split():
        shown = run("cat-file", "blob", f"{line}:{path}")
        if shown.returncode == 0:
            found_versions.append((CommitName(line), shown.stdout))
    return tuple(found_versions)
