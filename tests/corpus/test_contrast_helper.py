# SDD-EARS: CORPUS-112 CORPUS-113
"""The helper of Node that gives one request to swarm-verify, run here against a module that
stands in for swarm-verify and records what it is given; never against the corpus."""

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

from tests.corpus.contrast.sample import CONTRAST

INTEGRITY = (
    "sha512-"
    "xpAfXmNioZQVadKqldljIjLX6cAtLAqxqU08CFZ1Nu6Qt6Ha7saJBd0UZsTUksue5oTb/u2XnHcrhU95e8DlGw=="
)

STAND_IN = """
import { appendFileSync } from "node:fs";
const log = (what) => appendFileSync(process.env.STAND_IN_LOG, JSON.stringify(what) + "\\n");
export const requestVersion = "request-version";
export const verifierVersion = "verifier-version";
export async function sealFiles(input) {
  log({ call: "sealFiles", workspace: input.workspace, authority: input.authority,
        checks: input.checks,
        files: input.files.map((f) => ({ path: f.path, content: f.content.toString("utf8"),
                                          buffer: Buffer.isBuffer(f.content) })) });
}
export async function verify(request, options) {
  log({ call: "verify", request, options });
  return { state: "complete", regression: { status: "none" } };
}
"""


def test_the_package_pins_swarm_verify_by_version_and_integrity() -> None:
    package = json.loads((CONTRAST / "package.json").read_text())
    assert package["dependencies"] == {"swarm-verify": "3.1.0"}
    lock = json.loads((CONTRAST / "package-lock.json").read_text())
    pinned = lock["packages"]["node_modules/swarm-verify"]
    assert pinned["version"] == "3.1.0"
    assert pinned["integrity"] == INTEGRITY


def helper(tmp_path: Path, request: dict[str, Any]) -> tuple[str, list[dict[str, Any]]]:
    shutil.copy(CONTRAST / "run_arm.mjs", tmp_path / "run_arm.mjs")
    module = tmp_path / "node_modules" / "swarm-verify"
    module.mkdir(parents=True)
    (module / "package.json").write_text(
        json.dumps({"name": "swarm-verify", "type": "module", "exports": "./index.js"})
    )
    (module / "index.js").write_text(STAND_IN)
    log = tmp_path / "calls.jsonl"
    ended = subprocess.run(
        ["node", str(tmp_path / "run_arm.mjs")],
        input=json.dumps(request),
        capture_output=True,
        text=True,
        env={
            "PATH": "/usr/bin:/bin:" + str(Path(shutil.which("node") or "node").parent),
            "STAND_IN_LOG": str(log),
        },
        check=False,
    )
    assert ended.returncode == 0, ended.stderr
    calls = [json.loads(line) for line in log.read_text().splitlines()]
    return ended.stdout, calls


REQUEST: dict[str, Any] = {
    "repository": "/work/repository",
    "base": "a" * 40,
    "candidate": "b" * 40,
    "image": "ghcr.io/astral-sh/uv@sha256:" + "c" * 64,
    "out": "/work/evidence",
    "checks": [
        {
            "name": "dokime-visible",
            "command": "pytest",
            "kind": "test",
            "authority": "user-acceptance",
        }
    ],
    "sealed": None,
}


def test_the_helper_gives_the_request_to_verify_and_writes_its_result(tmp_path: Path) -> None:
    out, calls = helper(tmp_path, REQUEST)
    assert json.loads(out) == {"state": "complete", "regression": {"status": "none"}}
    (call,) = calls
    assert call["call"] == "verify"
    assert call["options"] == {"verifierVersion": "verifier-version"}
    request = call["request"]
    assert request["version"] == "request-version"
    assert request["repository"] == "/work/repository"
    assert request["base"] == {"commit": "a" * 40}
    assert request["candidate"] == {"kind": "commit", "commit": "b" * 40}
    assert request["checks"] == REQUEST["checks"]
    assert request["artifacts"] == {"directory": "/work/evidence"}
    assert request["policy"]["execution"]["image"] == REQUEST["image"]


def test_the_helper_seals_the_files_given_in_memory_before_it_verifies(tmp_path: Path) -> None:
    sealed = {
        "files": [{"path": "tests/dokime_held_out/examples/h1.json", "content": '{"á": 1}\n'}],
        "checks": [{"name": "held-out", "command": "pytest tests/dokime_held_out", "kind": "test"}],
    }
    _, calls = helper(tmp_path, {**REQUEST, "sealed": sealed})
    assert [call["call"] for call in calls] == ["sealFiles", "verify"]
    seal = calls[0]
    assert seal["workspace"] == "/work/repository"
    assert seal["authority"] == "user-acceptance"
    assert seal["checks"] == sealed["checks"]
    assert seal["files"] == [
        {"path": "tests/dokime_held_out/examples/h1.json", "content": '{"á": 1}\n', "buffer": True}
    ]
