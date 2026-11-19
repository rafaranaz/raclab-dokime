"""The versions of a file in the history of git (ADR-0014).

To find a held-out example that was once in clear, the audit reads every version of the contract of
a story in the history that its commit reaches. git runs as `checkout_commit` runs it: with the
environment of the adapter, which reads no configuration but that of the checkout, with the hooks
and the monitor of the file system turned off, and with the attributes read from the empty tree, so
that no filter they name changes the bytes read. The whole history is walked with
`--full-history`: without it, git follows only one parent of a merge that leaves the file as it was,
and misses a version in clear on a branch that took it back before the merge.

A failure of git, while it lists the commits or reads a version, is refused with `git-failed`, never
read as fewer versions, which would be fewer examples published.

These are limits, not guarantees: renames are not followed, so a version under an earlier path is
not seen; commits that only other refs reach are not read; and copies of an example in other files
are not looked for.
"""

import shutil
import subprocess
from pathlib import Path, PurePosixPath

from dokime.core.repository import CommitName, RefusalError
from dokime.platform.git import _EMPTY_TREE, _environment, file_versions

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

    def output(*args: str) -> bytes | None:
        done = run(*args)
        return done.stdout if done.returncode == 0 else None

    return file_versions(output, start, str(path))
