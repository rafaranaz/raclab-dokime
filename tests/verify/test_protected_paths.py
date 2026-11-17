# SDD-EARS: VERIFY-020 VERIFY-021 VERIFY-022 VERIFY-023 VERIFY-024 VERIFY-025 VERIFY-026 VERIFY-027
from pathlib import Path

import pytest

from dokime.contract.model import Contract
from dokime.core.findings import Finding
from dokime.core.verdicts import Verdict
from dokime.packs.model import Pack, Section
from dokime.verify.protected import protected_paths
from tests.verify.doubles import AuditedDouble, Files, patch

PACK = Pack(
    name="p",
    dockerfile=".dokime/Dockerfile",
    command=("pytest",),
    report="report.xml",
    test_paths=("tests/**",),
    config_paths=("conftest.py", "pytest.ini"),
    sections=(Section(file="pyproject.toml", format="toml", name="tool.pytest.ini_options"),),
)
PYPROJECT = '[project]\nname = "p"\n\n[tool.pytest.ini_options]\naddopts = "-q"\n'
BASE: Files = {
    "src/p.py": b"code",
    "tests/test_p.py": b"test",
    "conftest.py": b"config",
    "pyproject.toml": PYPROJECT.encode(),
    ".dokime/policy.yaml": b"policy",
}


def check(
    given: bytes, authorised: tuple[str, ...] = (), base: Files | None = None
) -> list[Finding]:
    repository = AuditedDouble()
    commit = repository.add(BASE if base is None else base)
    contract = Contract(
        story="S-1", may_modify_tests=authorised, requirements=(), examples=(), relations=()
    )
    result = protected_paths(PACK, contract, commit, given, repository)
    assert result.gate == "protected-paths"
    return list(result.findings)


def paths(findings: list[Finding]) -> list[str]:
    assert all(f.code == "protected-path" and f.verdict is Verdict.FAIL for f in findings)
    return [f.message.split(" ", 1)[0] for f in findings]


def test_a_patch_of_the_code_alone_passes() -> None:
    assert check(patch({"src/p.py": "new", "src/q.py": "added"}, ["src/p.py"])) == []


@pytest.mark.parametrize(
    ("given", "path"),
    [
        (patch({"tests/test_p.py": "edited"}), "tests/test_p.py"),
        (patch({"tests/test_new.py": "added"}), "tests/test_new.py"),
        (patch(removes=["tests/test_p.py"]), "tests/test_p.py"),
        (patch({"conftest.py": "edited"}), "conftest.py"),
        (patch({"pytest.ini": "[pytest]\n"}), "pytest.ini"),
    ],
    ids=["a-test-changed", "a-test-added", "a-test-removed", "config-changed", "config-added"],
)
def test_a_protected_path_that_the_patch_touches_is_a_finding(given: bytes, path: str) -> None:
    assert paths(check(given)) == [path]


def test_the_finding_says_why_the_path_is_protected() -> None:
    found = {
        f.message.split(" ", 1)[0]: f.message
        for f in check(patch({"tests/test_p.py": "x", "conftest.py": "y"}))
    }
    assert "a test of the pack" in found["tests/test_p.py"]
    assert "configuration of the tests" in found["conftest.py"]


def test_a_test_made_executable_is_a_change() -> None:
    assert paths(check(patch({"tests/test_p.py": ("x", "test")}))) == ["tests/test_p.py"]


def test_a_path_named_in_the_contract_is_authorised() -> None:
    given = patch({"tests/test_p.py": "edited", "conftest.py": "edited"})
    assert check(given, ("tests/test_p.py", "conftest.py")) == []


@pytest.mark.parametrize("entry", ["tests/**", "tests", "tests/", "./tests/test_p.py"])
def test_only_the_exact_path_is_authorised(entry: str) -> None:
    assert paths(check(patch({"tests/test_p.py": "edited"}), (entry,))) == ["tests/test_p.py"]


def test_a_mixed_file_whose_section_is_unchanged_passes() -> None:
    edited = PYPROJECT.replace('name = "p"', 'name = "q"')
    assert check(patch({"pyproject.toml": edited})) == []


def test_a_mixed_file_whose_section_changed_is_a_finding() -> None:
    edited = PYPROJECT.replace('"-q"', '"-q --deselect tests/test_p.py"')
    (found,) = check(patch({"pyproject.toml": edited}))
    assert paths([found]) == ["pyproject.toml"]
    assert "tool.pytest.ini_options" in found.message


def test_a_mixed_file_removed_with_its_section_is_a_finding() -> None:
    assert paths(check(patch(removes=["pyproject.toml"]))) == ["pyproject.toml"]


def test_a_mixed_file_named_in_the_contract_may_change_its_section() -> None:
    edited = PYPROJECT.replace('"-q"', '"-q -x"')
    assert check(patch({"pyproject.toml": edited}), ("pyproject.toml",)) == []


def test_the_directory_of_the_harness_is_protected_whatever_the_contract_says() -> None:
    given = patch({".dokime/policy.yaml": "edited", ".dokime/new.yaml": "added"})
    found = check(given, (".dokime/policy.yaml", ".dokime/new.yaml"))
    assert sorted(paths(found)) == [".dokime/new.yaml", ".dokime/policy.yaml"]
    assert all("harness" in f.message for f in found)


def test_a_test_replaced_by_a_link_to_the_same_bytes_is_a_change(tmp_path: Path) -> None:
    outside = tmp_path / "same"
    outside.write_bytes(b"test")
    assert paths(check(patch({"tests/test_p.py": ("->", str(outside))}))) == ["tests/test_p.py"]


def test_a_section_reached_through_a_link_is_not_read(tmp_path: Path) -> None:
    outside = tmp_path / "pyproject.toml"
    outside.write_text(PYPROJECT)
    assert paths(check(patch({"pyproject.toml": ("->", str(outside))}))) == ["pyproject.toml"]


def test_a_link_is_compared_by_its_target(tmp_path: Path) -> None:
    one, two = tmp_path / "one", tmp_path / "two"
    one.write_bytes(b"same")
    two.write_bytes(b"same")
    base = {**BASE, "tests/data": ("->", str(one))}
    assert check(patch({"tests/data": ("->", str(one))}), base=base) == []
    assert paths(check(patch({"tests/data": ("->", str(two))}), base=base)) == ["tests/data"]


def test_a_patch_that_does_not_apply_is_an_error() -> None:
    (found,) = check(patch(removes=["src/missing.py"]))
    assert (found.code, found.verdict) == ("patch-does-not-apply", Verdict.ERROR)
