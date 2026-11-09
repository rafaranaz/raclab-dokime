# SDD-EARS: REPO-070 REPO-071 REPO-072
import shlex
import sys
from pathlib import Path

from tests.repo.conftest import GitRunner, write
from tools.check_mermaid import check_files, has_mermaid, main

DIAGRAM = "# Doc\n\n```mermaid\nflowchart LR\n  A --> B\n```\n"
BROKEN = "# Doc\n\n```mermaid\nflowchart LR\n  A -->\n```\n"

FAKE_RENDERER = """\
import sys
from pathlib import Path

source = Path(sys.argv[sys.argv.index("-i") + 1]).read_text(encoding="utf-8")
if "A -->\\n" in source:
    print("Error: Parse error on line 2", file=sys.stderr)
    sys.exit(1)
"""


def fake_renderer(tmp_path: Path) -> list[str]:
    script = write(tmp_path, "fake_mmdc.py", FAKE_RENDERER)
    return [sys.executable, str(script)]


def test_detects_mermaid_blocks() -> None:
    assert has_mermaid(DIAGRAM)
    assert not has_mermaid("# Doc\n\n```python\nprint()\n```\n")


def test_accepts_files_the_renderer_accepts(tmp_path: Path) -> None:
    write(tmp_path, "docs/a.md", DIAGRAM)
    assert check_files(tmp_path, ["docs/a.md"], fake_renderer(tmp_path)) == []


def test_reports_the_renderer_error_for_rejected_files(tmp_path: Path) -> None:
    write(tmp_path, "docs/a.md", DIAGRAM)
    write(tmp_path, "docs/b.md", BROKEN)
    findings = check_files(tmp_path, ["docs/a.md", "docs/b.md"], fake_renderer(tmp_path))
    assert [f.path for f in findings] == ["docs/b.md"]
    assert "Parse error on line 2" in findings[0].message


def test_does_not_run_the_renderer_without_mermaid_blocks(tmp_path: Path) -> None:
    write(tmp_path, "docs/plain.md", "# Plain\n")
    assert check_files(tmp_path, ["docs/plain.md"], ["/nonexistent/mmdc"]) == []


def test_fails_when_the_renderer_cannot_be_run(tmp_path: Path) -> None:
    write(tmp_path, "docs/a.md", DIAGRAM)
    findings = check_files(tmp_path, ["docs/a.md"], ["/nonexistent/mmdc"])
    assert len(findings) == 1
    assert "/nonexistent/mmdc" in findings[0].message


def test_main_checks_tracked_markdown(repo: Path, git: GitRunner) -> None:
    write(repo, "docs/a.md", DIAGRAM)
    git(repo, "add", ".")
    renderer = shlex.join(fake_renderer(repo.parent))
    assert main(["--renderer", renderer], root=repo) == 0
    write(repo, "docs/b.md", BROKEN)
    git(repo, "add", ".")
    assert main(["--renderer", renderer], root=repo) == 1
