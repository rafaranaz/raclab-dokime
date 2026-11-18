# SDD-EARS: REPO-140 REPO-141 REPO-142 REPO-143 REPO-144 REPO-145 REPO-146
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


def test_the_pack_of_this_repository_passes_its_check() -> None:
    checked = check(PACK.read_text())
    assert checked.findings == ()
    assert checked.pack is not None
    assert checked.pack.dockerfile == "Dockerfile"


def test_the_base_image_is_named_by_its_digest() -> None:
    (base,) = [line for line in lines() if line.startswith("FROM ")]
    assert re.fullmatch(r"FROM [a-z0-9./-]+@sha256:[0-9a-f]{64}", base)


def test_every_package_has_the_version_of_the_lock_and_no_dependency_is_resolved() -> None:
    (install,) = [line for line in lines() if line.startswith("RUN pip install ")]
    words = shlex.split(install[len("RUN ") :])
    assert "--no-deps" in words
    pinned = dict(word.split("==") for word in words if "==" in word)
    locked = {
        package["name"]: package["version"]
        for package in tomllib.loads((ROOT / "uv.lock").read_text())["package"]
    }
    assert pinned
    assert {name: locked.get(name) for name in pinned} == pinned


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
    (install,) = [line for line in lines() if line.startswith("RUN pip install ")]
    pinned = {w.split("==")[0] for w in shlex.split(install[len("RUN ") :]) if "==" in w}
    packages = {
        package["name"]: package
        for package in tomllib.loads((ROOT / "uv.lock").read_text())["package"]
    }
    needed = {
        dependency["name"]
        for name in pinned
        for dependency in packages[name].get("dependencies", [])
        if "win32" not in dependency.get("marker", "")
        and "darwin" not in dependency.get("marker", "")
    }
    assert needed <= pinned, sorted(needed - pinned)


def test_an_error_in_the_collection_of_a_module_does_not_stop_the_others() -> None:
    checked = check(PACK.read_text())
    assert checked.pack is not None
    assert "--continue-on-collection-errors" in checked.pack.command
