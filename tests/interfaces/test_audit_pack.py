# SDD-EARS: INTERFACES-075 INTERFACES-076 INTERFACES-077 INTERFACES-079
from pathlib import Path

import pytest

from dokime.core.policy import Policy
from dokime.core.verdicts import Verdict
from dokime.interfaces.inputs import read_pack, read_tree_policy
from tests.interfaces.audits import DOCKERFILE, PACK, POLICY, base, tree


def test_the_pack_and_its_dockerfile_are_read_from_the_tree_of_the_base(tmp_path: Path) -> None:
    read = read_pack(base(tmp_path))
    assert (read.findings, read.text, read.dockerfile) == ((), PACK, DOCKERFILE)
    assert read.pack is not None
    assert read.pack.name == "python-semver"


def test_a_pack_given_from_outside_is_read_with_the_dockerfile_beside_it(tmp_path: Path) -> None:
    outside = tree(tmp_path / "pack", {"pack.yaml": PACK, "Dockerfile": b"FROM other\n"})
    read = read_pack(base(tmp_path / "base"), outside / "pack.yaml")
    assert (read.text, read.dockerfile) == (PACK, b"FROM other\n")


def test_the_findings_of_the_check_of_the_pack_are_given(tmp_path: Path) -> None:
    read = read_pack(base(tmp_path, **{".dokime__pack.yaml": b"format: 1\nname: p\n"}))
    assert read.findings
    assert read.pack is None


@pytest.mark.parametrize("dockerfile", ["../Dockerfile", "/etc/Dockerfile", "a/../../b"])
def test_a_dockerfile_outside_the_pack_is_refused_by_its_check(
    tmp_path: Path, dockerfile: str
) -> None:
    text = PACK.replace(b"dockerfile: Dockerfile", f"dockerfile: {dockerfile}".encode())
    read = read_pack(base(tmp_path, **{".dokime__pack.yaml": text}))
    assert [(f.code, f.verdict) for f in read.findings] == [("path-outside-pack", Verdict.FAIL)]
    assert read.dockerfile is None


def test_a_missing_dockerfile_is_named(tmp_path: Path) -> None:
    root = tree(tmp_path, {".dokime/pack.yaml": PACK})
    read = read_pack(root)
    assert [(f.code, f.verdict) for f in read.findings] == [("file-missing", Verdict.ERROR)]
    assert ".dokime/Dockerfile" in read.findings[0].message


def test_a_pack_from_outside_that_cannot_be_read_is_named(tmp_path: Path) -> None:
    read = read_pack(base(tmp_path / "base"), tmp_path / "absent" / "pack.yaml")
    assert [(f.code, f.verdict) for f in read.findings] == [("unreadable-file", Verdict.ERROR)]


def test_the_policy_of_the_base_is_read(tmp_path: Path) -> None:
    read = read_tree_policy(base(tmp_path, **{".dokime__policy.yaml": POLICY}))
    assert read.findings == ()
    assert read.policy == Policy(baseline_runs=3, verification_runs=4, from_file=True)


def test_a_base_without_a_policy_takes_the_defaults(tmp_path: Path) -> None:
    read = read_tree_policy(base(tmp_path))
    assert (read.findings, read.policy) == ((), Policy())


def test_a_policy_that_is_a_link_is_not_followed(tmp_path: Path) -> None:
    root = base(tmp_path / "base")
    (tmp_path / "policy.yaml").write_bytes(POLICY)
    (root / ".dokime" / "policy.yaml").symlink_to(tmp_path / "policy.yaml")
    read = read_tree_policy(root)
    assert [(f.code, f.verdict) for f in read.findings] == [("file-not-regular", Verdict.ERROR)]
    assert read.policy is None


def test_a_policy_with_a_finding_gives_its_findings_and_no_policy(tmp_path: Path) -> None:
    read = read_tree_policy(base(tmp_path, **{".dokime__policy.yaml": b"format: 1\nextra: 1\n"}))
    assert read.findings
    assert read.policy is None
