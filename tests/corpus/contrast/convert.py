"""Turn examples of a dokime contract into black-box checks that swarm-verify can run (R2, S2).

    uv run python -m tests.corpus.contrast.convert CONTRACT OUT EXAMPLE_ID...

writes the directory OUT, to be laid among the tests of a checkout so that its test check
collects it: the program that observes and the modules `core`, `contract`, `oracle` and `sandbox`
of dokime as they are, one JSON file for each example, `run.py` and `test_dokime_examples.py`.
"""

import json
import shutil
import sys
from pathlib import Path

from dokime.contract.check import check
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
    ignored = shutil.ignore_patterns("__pycache__", "README.md")
    (out / "dokime").mkdir(parents=True)
    shutil.copy(SOURCE / "__init__.py", out / "dokime" / "__init__.py")
    for module in MODULES:
        shutil.copytree(SOURCE / module, out / "dokime" / module, ignore=ignored)
    shutil.copy(SOURCE / "sandbox" / "observe_program.py", out / "observe_program.py")
    shutil.copy(HERE / "runner.py", out / "run.py")
    shutil.copy(HERE / "checks_file.py", out / "test_dokime_examples.py")
    (out / "examples").mkdir()
    for name in ids:
        text = json.dumps(encode(examples[name]), indent=2, ensure_ascii=False) + "\n"
        (out / "examples" / f"{name}.json").write_text(text, encoding="utf-8")


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
