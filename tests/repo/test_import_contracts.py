# SDD-EARS: REPO-100 REPO-101 REPO-102 REPO-103
import os
import re
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

from tests.repo.conftest import write
from tools._common import DEFAULT_ROOT

DIAGRAM = DEFAULT_ROOT / "docs/architecture/02-modules.md"
EDGE = re.compile(r"^\s+(\w+) --> (\w+)\s*$", re.MULTILINE)
LAYER_NAME = re.compile(r"\w+")

FORBIDDEN = [
    ("core", "contract"),
    ("contract", "oracle"),
    ("contract", "evidence"),
    ("evidence", "contract"),
    ("oracle", "packs"),
    ("verify", "spec"),
    ("verify", "engine"),
    ("verify", "sandbox"),
    ("engine", "platform"),
    ("sandbox", "contract"),
    ("sandbox", "agents"),
    ("platform", "engine"),
    ("gateway", "interfaces"),
    ("bench", "gateway"),
]


def _contracts_section() -> str:
    text = (DEFAULT_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    start = text.find("[tool.importlinter]")
    return text[start:] if start >= 0 else '[tool.importlinter]\nroot_package = "dokime"\n'


def _diagram_edges() -> set[tuple[str, str]]:
    return set(EDGE.findall(DIAGRAM.read_text(encoding="utf-8")))


def _diagram_modules() -> set[str]:
    return {name for edge in _diagram_edges() for name in edge}


def _lint(project: Path, imports: set[tuple[str, str]], modules: set[str]) -> int:
    """Build a package with the given modules and imports, and run the import check on it."""
    files = {}
    for module in sorted(modules):
        lines = [
            f"import dokime.{target}" for source, target in sorted(imports) if source == module
        ]
        files[f"{module}/__init__.py"] = "\n".join(lines) + "\n"
    return _lint_files(project, files)


def _lint_files(project: Path, files: dict[str, str]) -> int:
    """Write the given files under the package and run the import check on it."""
    write(project, "pyproject.toml", _contracts_section())
    write(project, "src/dokime/__init__.py", "")
    for relative, content in files.items():
        write(project, f"src/dokime/{relative}", content)
    result = subprocess.run(
        [sys.executable, "-c", "from importlinter.cli import lint_imports_command as c; c()"],
        cwd=project,
        env={**os.environ, "PYTHONPATH": str(project / "src")},
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode


def test_accepts_a_package_where_no_module_exists_yet(tmp_path: Path) -> None:
    assert _lint(tmp_path, set(), set()) == 0


def test_accepts_every_dependency_of_the_module_diagram(tmp_path: Path) -> None:
    assert _lint(tmp_path, _diagram_edges(), _diagram_modules()) == 0


@pytest.mark.parametrize(("source", "target"), FORBIDDEN)
def test_rejects_an_import_the_dependency_rules_forbid(
    tmp_path: Path, source: str, target: str
) -> None:
    assert _lint(tmp_path, {(source, target)}, _diagram_modules()) != 0


def test_rejects_a_forbidden_import_when_only_those_two_modules_exist(tmp_path: Path) -> None:
    assert _lint(tmp_path, {("contract", "verify")}, {"contract", "verify"}) != 0


def test_accepts_the_composition_root_importing_an_adapter_from_a_submodule(tmp_path: Path) -> None:
    files = {
        "bench/__init__.py": "import dokime.interfaces.cli\n",
        "interfaces/__init__.py": "",
        "interfaces/cli.py": "import dokime.sandbox.docker\n",
        "sandbox/__init__.py": "",
        "sandbox/docker.py": "",
    }
    assert _lint_files(tmp_path, files) == 0


def test_rejects_a_forbidden_import_between_submodules(tmp_path: Path) -> None:
    files = {
        "verify/__init__.py": "",
        "verify/gates.py": "import dokime.sandbox.docker\n",
        "sandbox/__init__.py": "",
        "sandbox/docker.py": "",
    }
    assert _lint_files(tmp_path, files) != 0


def test_rejects_the_bench_importing_an_adapter_from_a_submodule(tmp_path: Path) -> None:
    files = {
        "bench/__init__.py": "",
        "bench/run.py": "import dokime.gateway.client\n",
        "gateway/__init__.py": "",
        "gateway/client.py": "",
    }
    assert _lint_files(tmp_path, files) != 0


def test_the_contracts_name_the_same_modules_as_the_diagram() -> None:
    section = tomllib.loads(_contracts_section())["tool"]["importlinter"]
    named = {
        name
        for contract in section.get("contracts", [])
        for layer in contract["layers"]
        for name in LAYER_NAME.findall(layer)
    }
    assert named == _diagram_modules()
