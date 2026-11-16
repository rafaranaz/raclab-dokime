"""The cases of the corpus, each a directory `tests/corpus/<project>/cases/<case>/` (ADR-0055)."""

import tomllib
from dataclasses import dataclass
from pathlib import Path

from tests.corpus.projects import PROJECTS

GOOD = "good"
BAD_LABELS = ("fails-a-visible-example", "edits-tests", "breaks-existing-tests")
GATES = ("visible-examples", "protected-paths", "existing-tests")


@dataclass(frozen=True)
class Case:
    project: str
    name: str
    directory: Path

    @property
    def fields(self) -> dict[str, object]:
        with (self.directory / "case.toml").open("rb") as handle:
            return tomllib.load(handle)

    @property
    def good(self) -> bool:
        return self.fields.get("label") == GOOD

    @property
    def contract(self) -> Path:
        return (self.directory / str(self.fields["contract"])).resolve()

    @property
    def key(self) -> str:
        return f"{self.project}/{self.name}"


CASES = tuple(
    Case(project.name, path.name, path)
    for project in PROJECTS
    for path in sorted((project.directory / "cases").glob("*"))
    if path.is_dir()
)
