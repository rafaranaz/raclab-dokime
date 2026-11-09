# SDD-EARS: REPO-050
from pathlib import Path

from tests.repo.conftest import GitRunner, write
from tools.check_links import check_markdown, main

TRACKED = frozenset({"README.md", "docs/adr/README.md", "docs/adr/0001-x.md", "docs/ROADMAP.md"})


def test_accepts_existing_relative_links_files_and_directories() -> None:
    text = "[a](docs/ROADMAP.md) [b](docs/adr/) [c](docs/adr/0001-x.md#context) ![d](docs/adr)"
    assert check_markdown("README.md", text, TRACKED) == []


def test_resolves_links_relative_to_the_file() -> None:
    assert check_markdown("docs/adr/README.md", "[x](0001-x.md) [y](../ROADMAP.md)", TRACKED) == []


def test_ignores_external_links_anchors_and_code() -> None:
    text = (
        "[a](https://example.com) [b](#section) [c](mailto:a@b.c)\n"
        "`[d](missing.md)`\n```\n[e](missing.md)\n```\n"
    )
    assert check_markdown("README.md", text, TRACKED) == []


def test_reports_each_broken_link_with_its_line() -> None:
    text = "ok\n[a](docs/missing.md)\n[b](CONTINUAR_AQUI.md)\n"
    findings = check_markdown("README.md", text, TRACKED)
    assert [(f.line, f.message) for f in findings] == [
        (2, "broken link: docs/missing.md"),
        (3, "broken link: CONTINUAR_AQUI.md"),
    ]


def test_main_checks_tracked_markdown(repo: Path, git: GitRunner) -> None:
    write(repo, "README.md", "[r](docs/ROADMAP.md)\n")
    write(repo, "docs/ROADMAP.md", "roadmap\n")
    git(repo, "add", ".")
    assert main([], root=repo) == 0
    write(repo, "docs/ROADMAP.md", "[gone](nowhere.md)\n")
    assert main([], root=repo) == 1
