"""Turn examples of a dokime contract into black-box checks that swarm-verify can run (R2, S2).

    uv run python -m tests.corpus.contrast.convert CONTRACT OUT EXAMPLE_ID...

writes the directory OUT, to be laid among the tests of a checkout so that its test check
collects it: the program that observes and the modules `core`, `contract`, `oracle` and `sandbox`
of dokime as they are, one JSON file for each example, `run.py` and `test_dokime_examples.py`.
"""

import json
import sys
from collections.abc import Mapping
from pathlib import Path

from dokime.contract.check import check
from dokime.contract.model import Example
from tests.corpus.contrast.runner import encode

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parents[2] / "src" / "dokime"
MODULES = ("core", "contract", "oracle", "sandbox")


class ConversionError(Exception):
    """The conversion refused: the message says why, and nothing was written."""


def convert(contract_text: str, ids: list[str], out: Path) -> None:
    """Write into `out` the checks of the examples `ids` of the contract."""
    if out.exists():
        raise ConversionError(f"the directory {out} exists")
    checked = check(contract_text)
    if checked.contract is None:
        codes = ", ".join(finding.code for finding in checked.findings)
        raise ConversionError(f"the contract cannot be read: {codes}")
    examples = {example.id: example for example in checked.contract.examples}
    missing = [name for name in ids if name not in examples]
    if missing:
        raise ConversionError(f"no example of the contract has the id {', '.join(missing)}")
    for path, content in files_of({name: examples[name] for name in ids}).items():
        target = out / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)


def files_of(examples: Mapping[str, Example]) -> dict[str, bytes]:
    """The files of the conversion of `examples`, each under the name of its JSON file, by their
    path relative to the directory of the conversion, in memory."""
    files: dict[str, bytes] = {"dokime/__init__.py": (SOURCE / "__init__.py").read_bytes()}
    for module in MODULES:
        for path in sorted((SOURCE / module).rglob("*")):
            if path.is_file() and "__pycache__" not in path.parts and path.name != "README.md":
                files[f"dokime/{path.relative_to(SOURCE).as_posix()}"] = path.read_bytes()
    files["observe_program.py"] = (SOURCE / "sandbox" / "observe_program.py").read_bytes()
    files["run.py"] = (HERE / "runner.py").read_bytes()
    files["test_dokime_examples.py"] = (HERE / "checks_file.py").read_bytes()
    for name, example in examples.items():
        text = json.dumps(encode(example), indent=2, ensure_ascii=False) + "\n"
        files[f"examples/{name}.json"] = text.encode("utf-8")
    return files


def main(argv: list[str]) -> int:
    """Convert from the command line; a refusal is one line on the error output and code 2."""
    contract, out, *ids = argv[1:]
    try:
        convert(Path(contract).read_text(encoding="utf-8"), ids, Path(out))
    except ConversionError as refusal:
        sys.stderr.write(f"{refusal}\n")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
