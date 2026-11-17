"""The witnesses of a pack of the corpus, found with the candidates of the self-check (ADR-0057).

`witness_at` looks at one commit as the self-check does: its order, its candidates, the two sides
of a candidate and the rule of a witness are those of `packs`, run on the podman adapter. The test
of the witnesses of the good cases uses it.

Run by hand, the module goes on past the second witness, which the self-check does not:

    python -m tests.corpus.witnesses PROJECT CLONE COUNT

prints each of the first COUNT candidates of the history of CLONE, from its `HEAD`, and whether it
is a witness, with the tests it turned green. The measurement of ADR-0057 was taken this way, with
the tests run in a local environment instead of a container; its table is the fixture
`witnesses.toml`.
"""

import subprocess
import sys
import tempfile
from collections.abc import Iterator
from pathlib import Path

from dokime.core.repository import CommitName
from dokime.packs.check import check
from dokime.packs.loop import Candidate, _candidates
from dokime.platform.git import GitRepository
from dokime.sandbox.podman import PodmanRuntime
from tests.corpus.projects import Project


def candidates(project: Project, clone: Path, start: CommitName) -> Iterator[Candidate]:
    """The candidates of the history of the clone from a commit, in the order of the self-check."""
    pack = check(project.pack.read_text()).pack
    if pack is None:
        raise ValueError(f"the pack of {project.name} does not pass its check")
    with (
        tempfile.TemporaryDirectory(prefix="dokime-witnesses-") as work,
        GitRepository(clone) as repository,
    ):
        dockerfile = Path(work) / "Dockerfile"
        dockerfile.write_bytes((project.directory / pack.dockerfile).read_bytes())
        yield from _candidates(pack, dockerfile, start, repository, PodmanRuntime())


def witness_at(project: Project, clone: Path, commit: CommitName) -> Candidate:
    """The commit looked at as a candidate of the self-check, which has to be the first."""
    first = next(candidates(project, clone, commit), None)
    if first is None or first.commit != commit:
        raise ValueError(f"{commit.text} is not a candidate of the self-check of {project.name}")
    return first


def main(arguments: list[str]) -> None:
    from tests.corpus.projects import PROJECTS

    name, clone, count = arguments
    (project,) = [p for p in PROJECTS if p.name == name]
    head = subprocess.run(
        ["git", "-C", clone, "rev-parse", "HEAD"], capture_output=True, text=True, check=True
    ).stdout.strip()
    for position, candidate in enumerate(candidates(project, Path(clone), CommitName(head))):
        green = ", ".join(candidate.turned_green)
        print(f"{project.name} {candidate.commit.text} witness={candidate.witness} {green}")
        if position + 1 == int(count):
            break


if __name__ == "__main__":
    main(sys.argv[1:])
