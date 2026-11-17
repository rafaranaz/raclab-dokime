"""The trees and the files that the tests of the inputs of `audit` share."""

from pathlib import Path

CORPUS = Path(__file__).parents[1] / "corpus" / "python-semver"
STORY = "replace-keeps-the-constructor-error"
CONTRACT = (CORPUS / "cases" / STORY / "contract.yaml").read_bytes()
PACK = (CORPUS / "pack.yaml").read_bytes()
DOCKERFILE = b"FROM scratch\n"
POLICY = b"format: 1\nbaseline:\n  runs: 3\nverification:\n  runs: 4\n"
CONTRACT_PATH = f".dokime/changes/{STORY}/contract.yaml"


def tree(root: Path, files: dict[str, bytes]) -> Path:
    """A directory that stands for an extracted tree, with the files given."""
    root.mkdir(parents=True, exist_ok=True)
    for name, data in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    return root


def base(root: Path, **extra: bytes) -> Path:
    """A tree of a base with the contract of the story, the pack and its Dockerfile."""
    files = {
        CONTRACT_PATH: CONTRACT,
        ".dokime/pack.yaml": PACK,
        ".dokime/Dockerfile": DOCKERFILE,
        **{name.replace("__", "/"): data for name, data in extra.items()},
    }
    return tree(root, files)
