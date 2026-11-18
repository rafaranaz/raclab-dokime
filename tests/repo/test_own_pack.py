# SDD-EARS: REPO-140 REPO-141 REPO-142 REPO-143 REPO-144 REPO-145 REPO-146 REPO-147
import re
import shlex
import tomllib
from pathlib import Path

from dokime.packs.check import check

ROOT = Path(__file__).parents[2]
PACK = ROOT / ".dokime" / "pack.yaml"
DOCKERFILE = ROOT / ".dokime" / "Dockerfile"


def lines() -> list[str]:
    return DOCKERFILE.read_text().splitlines()


def normal(name: str) -> str:
    return name.lower().replace("_", "-")


def pinned() -> dict[str, str]:
    """The packages of the line that installs them, by their normal name, with their versions."""
    (install,) = [line for line in lines() if line.startswith("RUN pip install ") and "==" in line]
    words = shlex.split(install[len("RUN ") :])
    return {normal(w.split("==")[0]): w.split("==")[1] for w in words if "==" in w}


def backend() -> str:
    """The build backend that `pyproject.toml` requires."""
    project = tomllib.loads((ROOT / "pyproject.toml").read_text())
    (required,) = project["build-system"]["requires"]
    return normal(re.split(r"[<>=!~ ]", required, maxsplit=1)[0])


def test_the_pack_of_this_repository_passes_its_check() -> None:
    checked = check(PACK.read_text())
    assert checked.findings == ()
    assert checked.pack is not None
    assert checked.pack.dockerfile == "Dockerfile"


def test_the_base_image_is_named_by_its_digest() -> None:
    (base,) = [line for line in lines() if line.startswith("FROM ")]
    assert re.fullmatch(r"FROM [a-z0-9./-]+@sha256:[0-9a-f]{64}", base)


def test_every_package_has_the_version_of_the_lock_and_no_dependency_is_resolved() -> None:
    locked = {
        normal(package["name"]): package["version"]
        for package in tomllib.loads((ROOT / "uv.lock").read_text())["package"]
    }
    given = {name: version for name, version in pinned().items() if name != backend()}
    assert given
    assert {name: locked.get(name) for name in given} == given


def test_the_image_finds_the_source_of_the_project() -> None:
    paths = [
        value.split(":")
        for line in lines()
        if line.startswith("ENV ")
        for name, _, value in (part.partition("=") for part in shlex.split(line[4:]))
        if name == "PYTHONPATH"
    ]
    assert ["/dokime/project/src"] in [path[:1] for path in paths]


def test_the_configuration_of_the_tests_is_named() -> None:
    checked = check(PACK.read_text())
    assert checked.pack is not None
    assert "**/conftest.py" in checked.pack.config_paths
    sections = [(s.file, s.format, s.name) for s in checked.pack.sections]
    assert ("pyproject.toml", "toml", "tool.pytest.ini_options") in sections


def test_every_dependency_of_what_is_installed_is_installed() -> None:
    installed = set(pinned())
    packages = {
        normal(package["name"]): package
        for package in tomllib.loads((ROOT / "uv.lock").read_text())["package"]
    }
    needed = {
        normal(dependency["name"])
        for name in installed
        if name in packages
        for dependency in packages[name].get("dependencies", [])
        if "win32" not in dependency.get("marker", "")
        and "darwin" not in dependency.get("marker", "")
    }
    assert needed <= installed, sorted(needed - installed)


def test_an_error_in_the_collection_of_a_module_does_not_stop_the_others() -> None:
    checked = check(PACK.read_text())
    assert checked.pack is not None
    assert "--continue-on-collection-errors" in checked.pack.command


def test_the_project_is_installed_with_its_backend_at_an_exact_version() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text())
    (required,) = project["build-system"]["requires"]
    version = pinned()[backend()]
    major, minor = (int(part) for part in version.split(".")[:2])
    low, high = re.findall(r"(\d+)\.(\d+)", required)
    assert (int(low[0]), int(low[1])) <= (major, minor) < (int(high[0]), int(high[1]))
    assert "COPY . /dokime/build" in lines()
    assert "RUN pip install --no-cache-dir --no-deps --no-build-isolation /dokime/build" in lines()
