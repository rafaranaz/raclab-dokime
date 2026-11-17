# SDD-EARS: INTERFACES-085 INTERFACES-086 INTERFACES-087 INTERFACES-088 INTERFACES-089
import os
from pathlib import Path, PurePosixPath

import pytest

from dokime.core.findings import Finding
from dokime.core.repository import RefusalError
from dokime.core.verdicts import Verdict
from dokime.interfaces.inputs import (
    TREE_FILE_BYTES,
    read_contract,
    read_in_tree,
    read_pack,
    read_tree_policy,
)
from tests.interfaces.audits import CONTRACT, CONTRACT_PATH, STORY, base, tree


def refusal(tree_root: Path, path: str) -> Finding:
    with pytest.raises(RefusalError) as raised:
        read_in_tree(tree_root, PurePosixPath(path))
    assert raised.value.finding.verdict is Verdict.ERROR
    assert path in raised.value.finding.message
    return raised.value.finding


def test_a_file_of_the_tree_is_read(tmp_path: Path) -> None:
    assert read_in_tree(base(tmp_path), PurePosixPath(CONTRACT_PATH)) == CONTRACT


def test_a_link_as_the_file_is_not_followed(tmp_path: Path) -> None:
    root = tree(tmp_path / "tree", {})
    (tmp_path / "secret").write_bytes(b"secret")
    (root / "file").symlink_to(tmp_path / "secret")
    assert refusal(root, "file").code == "file-not-regular"


def test_a_link_as_a_directory_of_the_path_is_not_followed(tmp_path: Path) -> None:
    outside = tree(tmp_path / "outside", {f"changes/{STORY}/contract.yaml": CONTRACT})
    root = tree(tmp_path / "tree", {})
    (root / ".dokime").symlink_to(outside)
    assert refusal(root, CONTRACT_PATH).code == "file-not-regular"
    read = read_contract(root, story=STORY)
    assert [(f.code, f.verdict) for f in read.findings] == [("file-not-regular", Verdict.ERROR)]


def test_a_directory_or_a_fifo_is_not_a_regular_file(tmp_path: Path) -> None:
    root = tree(tmp_path, {"dir/inner": b""})
    os.mkfifo(root / "fifo")
    assert refusal(root, "dir").code == "file-not-regular"
    assert refusal(root, "fifo").code == "file-not-regular"


def test_a_missing_file_is_named(tmp_path: Path) -> None:
    root = tree(tmp_path, {})
    assert refusal(root, ".dokime/pack.yaml").code == "file-missing"
    read = read_pack(root)
    assert [(f.code, f.verdict) for f in read.findings] == [("file-missing", Verdict.ERROR)]


def test_a_file_beyond_its_bound_is_refused(tmp_path: Path) -> None:
    root = tree(tmp_path, {"big": b"x" * (TREE_FILE_BYTES + 1), "fits": b"x" * TREE_FILE_BYTES})
    assert refusal(root, "big").code == "file-too-large"
    assert read_in_tree(root, PurePosixPath("fits")) == b"x" * TREE_FILE_BYTES


@pytest.mark.parametrize("path", ["../outside", "/etc/passwd"])
def test_a_path_that_leaves_the_tree_is_refused(tmp_path: Path, path: str) -> None:
    assert refusal(tree(tmp_path, {}), path).code == "path-outside-tree"


def test_a_file_that_is_not_utf8_is_unreadable(tmp_path: Path) -> None:
    for read in (
        read_contract(
            base(tmp_path / "a", **{CONTRACT_PATH.replace("/", "__"): b"\xff"}), story=STORY
        ),
        read_pack(base(tmp_path / "b", **{".dokime__pack.yaml": b"\xff"})),
        read_tree_policy(base(tmp_path / "c", **{".dokime__policy.yaml": b"\xff"})),
    ):
        assert [(f.code, f.verdict) for f in read.findings] == [("unreadable-file", Verdict.ERROR)]


@pytest.mark.skipif(os.geteuid() == 0, reason="root reads a file without permissions")
def test_a_file_that_cannot_be_opened_is_unreadable(tmp_path: Path) -> None:
    root = tree(tmp_path, {"closed": b"x"})
    (root / "closed").chmod(0)
    try:
        assert refusal(root, "closed").code == "unreadable-file"
    finally:
        (root / "closed").chmod(0o600)
