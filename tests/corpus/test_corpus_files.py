# SDD-EARS: CORPUS-001 CORPUS-002 CORPUS-003 CORPUS-004 CORPUS-005
import re
import shlex

import pytest

from dokime.core.verdicts import Verdict
from dokime.packs.check import check
from tests.corpus.projects import PROJECTS, Project

PINNED_BASE = re.compile(r"FROM [a-z0-9./-]+@sha256:[0-9a-f]{64}")
EXACT = re.compile(r"[A-Za-z0-9_.-]+==[0-9][A-Za-z0-9_.+-]*")


def test_the_corpus_has_its_three_projects() -> None:
    assert [project.name for project in PROJECTS] == ["cachetools", "mdformat", "python-semver"]


@pytest.mark.parametrize("project", PROJECTS, ids=lambda p: p.name)
def test_a_project_holds_only_its_pack_its_dockerfile_its_source_and_its_cases(
    project: Project,
) -> None:
    names = {path.name for path in project.directory.iterdir()}
    assert (
        {"Dockerfile", "pack.yaml", "source.toml"}
        <= names
        <= {
            "Dockerfile",
            "cases",
            "pack.yaml",
            "source.toml",
        }
    )


@pytest.mark.parametrize("project", PROJECTS, ids=lambda p: p.name)
def test_the_source_names_the_repository_and_the_full_commit(project: Project) -> None:
    source = project.source
    assert set(source) == {"repository", "commit"}
    assert source["repository"].startswith("https://")
    assert re.fullmatch(r"[0-9a-f]{40}", source["commit"])


@pytest.mark.parametrize("project", PROJECTS, ids=lambda p: p.name)
def test_the_pack_passes_the_check_of_packs(project: Project) -> None:
    checked = check(project.pack.read_text(encoding="utf-8"))
    assert (checked.verdict, checked.findings) == (Verdict.PASS, ())


def instructions(project: Project, keyword: str) -> list[str]:
    lines = (project.directory / "Dockerfile").read_text().splitlines()
    return [line for line in lines if line.split(" ", 1)[0] == keyword]


@pytest.mark.parametrize("project", PROJECTS, ids=lambda p: p.name)
def test_the_base_image_is_named_by_its_digest(project: Project) -> None:
    (base,) = instructions(project, "FROM")
    assert PINNED_BASE.fullmatch(base), base


@pytest.mark.parametrize("project", PROJECTS, ids=lambda p: p.name)
def test_every_package_is_installed_at_an_exact_version_without_resolving_dependencies(
    project: Project,
) -> None:
    runs = instructions(project, "RUN")
    assert runs
    for run in runs:
        words = shlex.split(run)[1:]
        assert words[:2] == ["pip", "install"], run
        assert "--no-deps" in words, run
        packages = [word for word in words[2:] if not word.startswith("-")]
        assert packages, run
        assert all(EXACT.fullmatch(package) for package in packages), packages
