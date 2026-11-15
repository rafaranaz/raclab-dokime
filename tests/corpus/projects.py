"""The projects of the corpus, each a directory with its pack, its Dockerfile and its source."""

import tomllib
from dataclasses import dataclass
from pathlib import Path

HERE = Path(__file__).parent


@dataclass(frozen=True)
class Project:
    name: str
    directory: Path

    @property
    def source(self) -> dict[str, str]:
        with (self.directory / "source.toml").open("rb") as handle:
            return tomllib.load(handle)

    @property
    def pack(self) -> Path:
        return self.directory / "pack.yaml"


PROJECTS = tuple(
    Project(path.name, path) for path in sorted(HERE.iterdir()) if (path / "source.toml").exists()
)
