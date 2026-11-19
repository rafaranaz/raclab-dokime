# SDD-EARS: REPO-159
import ast
from pathlib import Path

ROOT = Path(__file__).parents[2]
PACKAGE = ROOT / "src" / "dokime"


def importers(package: Path) -> list[str]:
    """The modules of a package that import pyrage, as paths relative to the package."""
    found = []
    for path in sorted(package.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            names = []
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                names = [node.module]
            if any(name == "pyrage" or name.startswith("pyrage.") for name in names):
                found.append(path.relative_to(package).as_posix())
                break
    return found


def test_only_platform_imports_pyrage() -> None:
    assert [m for m in importers(PACKAGE) if not m.startswith("platform/")] == []


def test_an_import_of_pyrage_outside_platform_is_found(tmp_path: Path) -> None:
    (tmp_path / "platform").mkdir()
    (tmp_path / "platform" / "sealed.py").write_text("import pyrage\n")
    (tmp_path / "verify").mkdir()
    (tmp_path / "verify" / "gate.py").write_text("from pyrage import x25519\n")
    (tmp_path / "oracle").mkdir()
    (tmp_path / "oracle" / "split.py").write_text("import random\n")
    assert importers(tmp_path) == ["platform/sealed.py", "verify/gate.py"]
