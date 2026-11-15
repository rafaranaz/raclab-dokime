"""The container engines that the tests of the verification runtime adapters use.

A test that needs an engine skips when the engine is not installed, except in CI, where it fails:
the guarantees of ADR-0043 must be proven there, not skipped in silence.
"""

import os
import shutil
import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import pytest

from dokime.core.findings import Finding
from dokime.core.repository import RefusalError
from dokime.core.runtime import Digest, VerificationRuntime
from dokime.sandbox.podman import PodmanRuntime

BUSYBOX_INDEX = "sha256:73aaf090f3d85aa34ee199857f03fa3a95c8ede2ffd4cc2cdb5b94e566b11662"
"""The index of `busybox:1.36`, so that every engine and every version starts from the same one."""
BUSYBOX = f"docker.io/library/busybox@{BUSYBOX_INDEX}"
BUSYBOX_PLATFORMS = {
    "x86_64": Digest("sha256:b7f3d86d6e84fc17718c48bcde1450807faa2d56704205c697b4bd5df7b9e29f"),
}
"""The manifest of each platform in that index, read in the store of podman 5.4.2."""
PYTHON = "docker.io/library/python:3.13-slim"


def require(engine: str) -> str:
    """The absolute path of an engine; a skip when it is missing, a failure when in CI."""
    found = shutil.which(engine)
    if found is None:
        if os.environ.get("CI"):
            pytest.fail(f"{engine} is not installed, and a test of an engine cannot skip in CI")
        pytest.skip(f"{engine} is not installed")
    return found


@dataclass(frozen=True)
class Engine:
    """An engine, driven by its command line, to prepare and inspect what an adapter does."""

    name: str
    adapter: Callable[[], VerificationRuntime]

    def command(self, *args: str, check: bool = True) -> str:
        done = subprocess.run(
            [require(self.name), *args], capture_output=True, text=True, check=False
        )
        if check and done.returncode != 0:
            raise AssertionError(f"{self.name} {' '.join(args)}: {done.stderr}")
        return done.stdout.strip()

    def pull(self, reference: str) -> Digest:
        if not self.exists(reference):
            self.command("pull", "--quiet", reference)
        return Digest(
            "sha256:" + self.command("image", "inspect", "--format", "{{.Id}}", reference)
        )

    def exists(self, reference: str) -> bool:
        done = subprocess.run(
            [require(self.name), "image", "exists", reference], capture_output=True, check=False
        )
        return done.returncode == 0

    def read(self, image: Digest, path: str) -> str:
        return self.command("run", "--rm", "--network", "none", image.text, "cat", path)

    def containers(self) -> set[str]:
        """The identifiers of every container of the engine, running or not, builds included."""
        listed = self.command("ps", "--all", "--external", "--no-trunc", "--format", "{{.ID}}")
        return set(listed.split())


ENGINES = {"podman": Engine("podman", PodmanRuntime)}
"""Every engine with an adapter: a test of the port runs over all of them."""


def refusal(action: Callable[[], object]) -> Finding:
    with pytest.raises(RefusalError) as raised:
        action()
    return raised.value.finding


def project_with(directory: Path, files: dict[str, str]) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    for name, text in files.items():
        (directory / name).write_text(text)
    return directory
