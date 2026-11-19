"""A clean checkout with its recipients, an approved contract outside it, and a run of the seal."""

import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

from dokime.core.layout import contract_path, sealed_path
from dokime.interfaces.cli import main
from dokime.platform.sealed_store import create_identity, load_identity
from dokime.verify.sealed import Batch, read_batch

STORY = "add-one"
PASSPHRASE = "a passphrase for the tests"  # noqa: S105 - of a test identity, made and dropped here
REQUIREMENT = "When the function is called with a number, the function shall return it plus one."


def example(name: str, case: str, argument: int) -> str:
    return (
        f"  - id: {name}\n    requirement: R-add\n    case: {case}\n    boundary: function\n"
        f"    target: p:f\n    origin: human\n    steps:\n"
        f"      - input: {{args: [{argument}]}}\n        expect: {{returns: {argument + 1}}}\n"
    )


EXAMPLES = (
    example("E-a1", "c1", 1)
    + example("E-a2", "c1", 2)
    + example("E-b1", "c2", 3)
    + example("E-c1", "c3", 4)
    + example("E-c2", "c3", 5)
)
HELD = {
    "E-a1": example("E-a1", "c1", 1),
    "E-a2": example("E-a2", "c1", 2),
    "E-c1": example("E-c1", "c3", 4),
    "E-c2": example("E-c2", "c3", 5),
}


def contract(examples: str = EXAMPLES, story: str = STORY) -> str:
    return (
        f"format: 1\nstory: {story}\nmay_modify_tests: []\nrequirements:\n"
        f"  - id: R-add\n    kind: new\n    text: {REQUIREMENT}\n    source: written\n"
        f"examples:\n{examples}"
    )


def git(project: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(project), "-c", "user.name=t", "-c", "user.email=t@example.com", *args],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()


@dataclass
class Place:
    """Where a seal runs: the checkout, the approved contract, `--out` and the identity."""

    project: Path
    approved: Path
    out: Path
    identity: Path
    recipient: str


def place(root: Path, *, history: tuple[str, ...] = ()) -> Place:
    """A clean checkout whose HEAD has the recipients, after the given versions of the contract."""
    root.mkdir(parents=True, exist_ok=True)
    identity = root / "keys" / "identity.age"
    recipient = create_identity(identity, PASSPHRASE)
    project = root / "project"
    project.mkdir()
    git(project, "init", "--quiet", "--initial-branch=main")
    for version in history:
        target = project / str(contract_path(STORY))
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(version)
        git(project, "add", "--all")
        git(project, "commit", "--quiet", "--message", "a version of the contract")
    (project / ".dokime").mkdir(exist_ok=True)
    (project / ".dokime" / "recipients.txt").write_text(f"# the maintainer\n{recipient}\n")
    (project / "src").mkdir()
    (project / "src" / "p.py").write_text("def f(x):\n    return x\n")
    git(project, "add", "--all")
    git(project, "commit", "--quiet", "--message", "the recipients")
    approved = root / "approved" / "contract.yaml"
    approved.parent.mkdir()
    approved.write_text(contract())
    return Place(project, approved, root / "out", identity, recipient)


def seal(where: Place, answer: str | None = "y\n", *extra: str) -> int:
    """Run the seal, with the answer of the confirmation through a descriptor."""
    arguments = [
        "contract",
        "seal",
        "--story",
        STORY,
        "--contract",
        str(where.approved),
        "--out",
        str(where.out),
        "--project",
        str(where.project),
        *extra,
    ]
    if answer is None:
        return main(arguments)
    read, write = os.pipe()
    os.write(write, answer.encode())
    os.close(write)
    try:
        return main([*arguments, "--recipients-confirmed-by-fd", str(read)])
    finally:
        os.close(read)


def opened(where: Place) -> Batch:
    """The batch of the seal, opened with the identity of the place."""
    store, _ = load_identity(where.identity, PASSPHRASE)
    return read_batch(store.open((where.project / str(sealed_path(STORY))).read_bytes()))


def events(where: Place) -> list[dict[str, object]]:
    return [json.loads(line) for line in (where.out / "ledger.jsonl").read_text().splitlines()]
