# SDD-EARS: CORPUS-114 CORPUS-115 CORPUS-116 CORPUS-117 CORPUS-118 CORPUS-119
"""The command of the runs of R2, run here on a small project of its own with an identity and a
batch made for the test, and a helper that stands in for the one of Node; never with a sealed
batch of the corpus."""

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from dokime.platform.sealed_store import AgeSealedStore, create_identity, load_identity
from dokime.verify.sealed import Batch, Canary, SealedExample, batch_bytes
from tests.corpus.cases import ACTIVE
from tests.corpus.contrast import maintainer
from tests.corpus.contrast.maintainer import ARMS, Spec, run_arm, specs
from tests.corpus.contrast.runs import HELD_OUT, VISIBLE, check_command
from tests.corpus.contrast.sample import CONTRACT, PROJECT

HELD_ID = "E-held-7f3a91"
"""The id of the held-out example of the test batch, which no file written by the command holds."""
HELD_TEXT = (
    f"  - id: {HELD_ID}\n    requirement: adds\n    case: sum\n    boundary: function\n"
    "    target: proj:add\n    origin: human\n    steps:\n"
    "      - input: {args: [7139, 2]}\n        expect: {returns: 7141}\n"
)
TEST = "python -m pytest -p no:cacheprovider -q tests"
ADAPTATION = {
    "image": "ghcr.io/astral-sh/uv@sha256:" + "c" * 64,
    "setup": "true",
    "test": TEST,
    "minutes": 0,
    "files": {
        "swarm.toml": "\n[verify]\nsetup = 'true'\n",
        "gen.txt": "generate: echo made > gen.txt",
    },
}
WITNESS_TEST = "def test_add():\n    from proj import add\n    assert add(1, 2) == 3\n"
NEW_TEST = "def test_new():\n    pass\n"

STAND_IN = r"""
import json, os, subprocess, sys
from pathlib import Path

request = json.loads(sys.stdin.read())
repository = Path(request["repository"])
def git(*args):
    return subprocess.run(["git", *args], cwd=repository, capture_output=True, text=True).stdout
found = [
    str(path) for path in repository.rglob("*")
    if path.is_file() and ".git" not in path.parts and HELD_ID.encode() in path.read_bytes()
]
home = os.environ["SWARM_HOME"]
record = {
    "request": request,
    "stdin_holds_secret": HELD_ID in json.dumps(request),
    "home": home,
    "home_existed": os.path.isdir(home),
    "base_files": git("ls-tree", "-r", "--name-only", request["base"]).split(),
    "candidate_proj": git("show", request["candidate"] + ":proj.py"),
    "swarm_toml": git("show", request["base"] + ":swarm.toml"),
    "found_in_copy": found,
}
with open(os.environ["STAND_IN_LOG"], "a") as log:
    log.write(json.dumps(record) + "\n")
out = Path(request["out"])
out.mkdir(parents=True)
(out / "observations.json").write_text(json.dumps({"checks": [], "sealed": []}))
print(json.dumps({"state": "complete", "regression": {"status": "none"}}))
sys.exit(int(os.environ.get("STAND_IN_EXIT", "0")))
"""


def git(directory: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=directory,
        env={**os.environ, **maintainer.AUTHOR},
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()


@pytest.fixture
def opened(tmp_path: Path) -> tuple[AgeSealedStore, Path]:
    """A disposable identity, and a test batch sealed for it that holds out one example."""
    path = tmp_path / "identity" / "identity.age"
    recipient = create_identity(path, "a disposable passphrase")
    store, findings = load_identity(path, "a disposable passphrase")
    assert not findings
    batch = Batch(
        story="contrast",
        base="d" * 40,
        seed=1,
        order=("E-1", "E-2", "E-3", "E-4", "E-5", "E-6", HELD_ID),
        kept_visible=(),
        examples=(SealedExample(HELD_ID, bytes(16), HELD_TEXT),),
        unheld=(),
        canary=Canary(id="E-canary", of=HELD_ID, expected="0" * 32),
    )
    sealed = tmp_path / "batch" / "sealed.age"
    sealed.parent.mkdir()
    sealed.write_bytes(store.seal(batch_bytes(batch), [recipient]))
    return store, sealed


@pytest.fixture
def spec(tmp_path: Path, opened: tuple[AgeSealedStore, Path]) -> Spec:
    origin = tmp_path / "origin"
    (origin / "tests").mkdir(parents=True)
    (origin / "proj.py").write_text(PROJECT)
    (origin / "tests" / "test_proj.py").write_text("def test_nothing():\n    pass\n")
    git(origin, "init", "-q")
    git(origin, "add", "-A")
    git(origin, "commit", "-q", "-m", "base")
    base = git(origin, "rev-parse", "HEAD")
    (origin / "tests" / "test_proj.py").write_text(WITNESS_TEST)
    (origin / "tests" / "test_new.py").write_text(NEW_TEST)
    (origin / "README").write_text("the witness\n")
    git(origin, "add", "-A")
    git(origin, "commit", "-q", "-m", "witness")
    witness = git(origin, "rev-parse", "HEAD")
    patch = (
        b"--- a/proj.py\n+++ b/proj.py\n@@ -1,2 +1,3 @@\n \n+# the patch of the case\n"
        b" import uuid\n"
    )
    return Spec(
        key="sample/a-case",
        origin=str(origin),
        base=base,
        patch=patch,
        adaptation=ADAPTATION,
        contract=CONTRACT,
        sealed=opened[1],
        witness=witness,
        turned_green=("tests.test_proj::test_add",),
        pack_paths=("tests/**",),
    )


def stand_in(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[list[str], Path]:
    script = tmp_path / "stand_in.py"
    script.write_text(f"HELD_ID = {HELD_ID!r}\n" + STAND_IN)
    log = tmp_path / "calls.jsonl"
    monkeypatch.setenv("STAND_IN_LOG", str(log))
    return [sys.executable, str(script)], log


def ran(log: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in log.read_text().splitlines()] if log.exists() else []


def run(
    spec: Spec,
    arm: str,
    opened: tuple[AgeSealedStore, Path],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> dict[str, Any]:
    helper, log = stand_in(tmp_path, monkeypatch)
    entry = run_arm(spec, arm, opened[0].open, tmp_path / "out", helper)
    assert entry.failure == "", entry
    (record,) = ran(log)
    return record


def test_without_the_identity_the_command_refuses_and_runs_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    helper, log = stand_in(tmp_path, monkeypatch)
    for environ in ({}, {"DOKIME_CORPUS_IDENTITY": str(tmp_path / "missing.age")}):
        code = maintainer.main(
            [str(tmp_path / "out"), str(tmp_path / "results.toml")],
            environ=environ,
            passphrase=lambda: pytest.fail("asked for a passphrase"),
            helper=helper,
        )
        assert code == 2
        assert "DOKIME_CORPUS_IDENTITY" in capsys.readouterr().err
    assert ran(log) == []
    assert not (tmp_path / "results.toml").exists()


def test_the_command_runs_three_arms_on_each_case_that_is_not_withdrawn() -> None:
    assert ARMS == ("S0", "S1", "S2")
    found = specs()
    assert [spec.key for spec in found] == [case.key for case in ACTIVE]
    assert len(found) == 32


def test_each_run_is_a_local_copy_with_the_adaptation_and_the_patch_on_top(
    spec: Spec,
    opened: tuple[AgeSealedStore, Path],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    record = run(spec, "S0", opened, tmp_path, monkeypatch)
    assert {"swarm.toml", "gen.txt", "proj.py", "tests/test_proj.py"} <= set(record["base_files"])
    assert "# the patch of the case" in record["candidate_proj"]
    assert record["request"]["repository"] != spec.origin
    assert record["request"]["image"] == ADAPTATION["image"]
    assert record["request"]["checks"] == []
    assert record["request"]["sealed"] is None
    assert record["request"]["out"] == str(tmp_path / "out" / "sample--a-case" / "S0")


def test_each_run_has_a_swarm_home_of_its_own_deleted_when_it_ends(
    spec: Spec,
    opened: tuple[AgeSealedStore, Path],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    helper, log = stand_in(tmp_path, monkeypatch)
    for arm in ARMS:
        run_arm(spec, arm, opened[0].open, tmp_path / "out", helper)
    records = ran(log)
    homes = [record["home"] for record in records]
    assert all(record["home_existed"] for record in records)
    assert len(set(homes)) == 3
    assert not any(Path(home).exists() for home in homes)


def test_s1_seals_the_test_files_that_the_witness_changed_as_at_the_witness(
    spec: Spec,
    opened: tuple[AgeSealedStore, Path],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sealed = run(spec, "S1", opened, tmp_path, monkeypatch)["request"]["sealed"]
    assert sealed["files"] == [
        {"path": "tests/test_new.py", "content": NEW_TEST},
        {"path": "tests/test_proj_witness.py", "content": WITNESS_TEST},
    ]
    (check,) = sealed["checks"]
    assert check["command"] == TEST
    assert check["kind"] == "test"


def test_s1_seals_no_file_at_a_path_that_the_base_tracks(
    spec: Spec,
    opened: tuple[AgeSealedStore, Path],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    record = run(spec, "S1", opened, tmp_path, monkeypatch)
    sealed = {file["path"] for file in record["request"]["sealed"]["files"]}
    assert sealed.isdisjoint(record["base_files"])


def test_s2_lays_the_visible_examples_in_the_base_and_seals_the_held_out_ones(
    spec: Spec,
    opened: tuple[AgeSealedStore, Path],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    record = run(spec, "S2", opened, tmp_path, monkeypatch)
    for name in ("E-1", "E-6"):
        assert f"{VISIBLE}/examples/{name}.json" in record["base_files"]
    assert not any(path.startswith(HELD_OUT) for path in record["base_files"])
    (check,) = record["request"]["checks"]
    assert check["authority"] == "user-acceptance"
    assert check["command"] == check_command(TEST, [VISIBLE])
    sealed = record["request"]["sealed"]
    paths = [file["path"] for file in sealed["files"]]
    assert f"{HELD_OUT}/examples/h1.json" in paths
    assert all(path.startswith(f"{HELD_OUT}/") and HELD_ID not in path for path in paths)
    (example,) = [f for f in sealed["files"] if f["path"].endswith("h1.json")]
    assert HELD_ID in example["content"]
    assert "E-canary" not in json.dumps(sealed)
    assert sealed["checks"][0]["command"] == check_command(TEST, [HELD_OUT])


def test_a_case_without_a_batch_seals_nothing_in_s2(
    spec: Spec,
    opened: tuple[AgeSealedStore, Path],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    unsealed = Spec(**{**spec.__dict__, "sealed": None})
    assert run(unsealed, "S2", opened, tmp_path, monkeypatch)["request"]["sealed"] is None


def test_the_held_out_examples_reach_the_helper_only_through_its_input(
    spec: Spec,
    opened: tuple[AgeSealedStore, Path],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    record = run(spec, "S2", opened, tmp_path, monkeypatch)
    assert record["stdin_holds_secret"] is True
    assert record["found_in_copy"] == []
    log = Path(os.environ["STAND_IN_LOG"])
    written = [
        path
        for path in tmp_path.rglob("*")
        if path.is_file() and path != log and HELD_ID.encode() in path.read_bytes()
    ]
    assert written == [tmp_path / "stand_in.py"]


def test_a_patch_that_does_not_apply_is_a_failure_of_the_mount(
    spec: Spec,
    opened: tuple[AgeSealedStore, Path],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    helper, log = stand_in(tmp_path, monkeypatch)
    broken = Spec(
        **{**spec.__dict__, "patch": b"--- a/none.py\n+++ b/none.py\n@@ -1 +1 @@\n-a\n+b\n"}
    )
    entry = run_arm(broken, "S0", opened[0].open, tmp_path / "out", helper)
    assert entry.failure == "mount"
    assert ran(log) == []


def test_a_helper_that_ends_with_an_error_is_a_failure_of_the_helper(
    spec: Spec,
    opened: tuple[AgeSealedStore, Path],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    helper, _ = stand_in(tmp_path, monkeypatch)
    monkeypatch.setenv("STAND_IN_EXIT", "1")
    entry = run_arm(spec, "S2", opened[0].open, tmp_path / "out", helper)
    assert entry.failure == "helper"
