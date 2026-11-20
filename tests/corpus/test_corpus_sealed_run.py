# SDD-EARS: CORPUS-069 CORPUS-071
"""The sealed run of B1 in CI: a sealed contract audited without the key, and a sealed audit whose
calls of git and podman are logged to show that the identity and its passphrase stay out of them."""

import json
import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path
from typing import Any

from dokime.platform.sealed_store import create_identity
from tests.corpus.cases import CASES
from tests.corpus.clones import clone, skip_unless_asked
from tests.corpus.projects import PROJECTS
from tests.sandbox.engines import require

HERE = Path(__file__).parent / "holdout-by-hand"
NAME = "replace-keeps-the-constructor-error"
PASSPHRASE = "a passphrase made for this test only"  # noqa: S105 - of a test identity, made here


def git(directory: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(directory), "-c", "user.name=t", "-c", "user.email=t@example.com", *args],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()


def checkout(tmp_path: Path) -> tuple[Path, Path]:
    """A clone of python-semver on the base of the case, and its pack."""
    (case,) = [c for c in CASES if c.key == f"python-semver/{NAME}"]
    (project,) = [p for p in PROJECTS if p.name == "python-semver"]
    directory = clone(project, tmp_path / "project")
    git(directory, "checkout", "--quiet", "-b", "sealed", str(case.fields["base"]))
    return directory, project.pack


def commit(directory: Path, files: dict[str, bytes], message: str) -> str:
    for name, data in files.items():
        target = directory / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    git(directory, "add", "--all")
    git(directory, "commit", "--quiet", "--message", message)
    return git(directory, "rev-parse", "HEAD")


def audit(
    tmp_path: Path,
    directory: Path,
    pack: Path,
    base: str,
    *extra: str,
    env: dict[str, str] | None = None,
    pass_fds: tuple[int, ...] = (),
) -> dict[str, Any]:
    temporary = tmp_path / "temporary"
    temporary.mkdir(exist_ok=True)
    done = subprocess.run(
        [
            sys.executable,
            "-m",
            "dokime.interfaces",
            "audit",
            "--project",
            str(directory),
            "--base",
            base,
            "--patch",
            str(HERE / "patches" / f"{NAME}.minimal.diff"),
            "--story",
            NAME,
            "--pack",
            str(pack),
            "--out",
            str(tmp_path / "out"),
            "--format",
            "json",
            *extra,
        ],
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, "TMPDIR": str(temporary), **(env or {})},
        pass_fds=pass_fds,
        timeout=3600,
    )
    result: dict[str, Any] = json.loads(done.stdout)
    return result


def sealed_gate(result: dict[str, Any]) -> dict[str, Any]:
    (gate,) = [g for g in result["gates"] if g["gate"] == "sealed-examples"]
    found: dict[str, Any] = gate
    return found


def test_a_sealed_contract_without_the_key_is_not_applicable_as_the_key_is_not_here(
    tmp_path: Path,
) -> None:
    skip_unless_asked()
    require("git")
    require("podman")
    directory, pack = checkout(tmp_path)
    sealed = HERE / "sealed-run" / NAME
    base = commit(
        directory,
        {
            f".dokime/changes/{NAME}/contract.yaml": (sealed / "contract.yaml").read_bytes(),
            f".dokime/changes/{NAME}/sealed.age": (sealed / "sealed.age").read_bytes(),
        },
        "the sealed contract of the measurement of B1",
    )
    nowhere = tmp_path / "no-data-home"
    result = audit(tmp_path, directory, pack, base, env={"XDG_DATA_HOME": str(nowhere)})
    print(f"sealed contract without the key: verdict {result['verdict']}, {sealed_gate(result)}")
    assert result["verdict"] == "PASS"
    assert sealed_gate(result) == {
        "gate": "sealed-examples",
        "status": "not-applicable",
        "reason": "the key is not here",
    }


def shims(directory: Path, log: Path) -> Path:
    """Wrappers of git and podman that log the arguments, the environment, the descriptors and the
    files of a build context of each call, then run the real program."""
    directory.mkdir()
    log.mkdir()
    for program in ("git", "podman"):
        real = shutil.which(program)
        assert real is not None
        script = directory / program
        script.write_text(
            "#!/bin/bash\n"
            f'out="{log}/$(date +%s%N).$$.{program}"\n'
            '{ for a in "$@"; do printf "ARG %s\\n" "$a"; done; env | sed "s/^/ENV /"\n'
            '  ls -l /proc/$$/fd 2>/dev/null | sed "s/^/FD /"\n'
            f'  if [ "{program}" = podman ] && [ "$1" = build ]; then\n'
            '    for a in "$@"; do [ -d "$a" ] && find "$a" -type f | sed "s/^/CTX /"\n'
            '    [ -d "$a" ] && grep -rl -F "$PASSPHRASE_PROBE" "$a" | sed "s/^/LEAK /"; done; fi\n'
            '} > "$out"\n'
            f'exec "{real}" "$@"\n'
        )
        script.chmod(script.stat().st_mode | stat.S_IXUSR)
    return directory


def test_the_identity_its_passphrase_and_its_descriptor_stay_out_of_git_and_podman(
    tmp_path: Path,
) -> None:
    skip_unless_asked()
    require("git")
    require("podman")
    directory, pack = checkout(tmp_path)
    keys = tmp_path / "keys"
    identity = keys / "identity.age"
    recipient = create_identity(identity, PASSPHRASE)
    commit(directory, {".dokime/recipients.txt": f"{recipient}\n".encode()}, "the recipients")
    whole = tmp_path / "approved" / "contract.yaml"
    whole.parent.mkdir()
    whole.write_bytes((HERE / "python-semver" / NAME / "contract.yaml").read_bytes())
    confirm, answer = os.pipe()
    os.write(answer, b"y\n")
    os.close(answer)
    try:
        sealing = subprocess.run(
            [
                sys.executable,
                "-m",
                "dokime.interfaces",
                "contract",
                "seal",
                "--story",
                NAME,
                "--contract",
                str(whole),
                "--out",
                str(tmp_path / "seal"),
                "--project",
                str(directory),
                "--recipients-confirmed-by-fd",
                str(confirm),
            ],
            capture_output=True,
            text=True,
            check=False,
            pass_fds=(confirm,),
            timeout=600,
        )
    finally:
        os.close(confirm)
    assert sealing.returncode == 0, sealing.stdout + sealing.stderr
    git(directory, "add", "--all")
    git(directory, "commit", "--quiet", "--message", "the sealed contract")
    base = git(directory, "rev-parse", "HEAD")
    log = tmp_path / "calls"
    wrappers = shims(tmp_path / "shims", log)
    secret, write = os.pipe()
    os.write(write, f"{PASSPHRASE}\n".encode())
    os.close(write)
    os.set_inheritable(secret, True)
    pipe = f"pipe:[{os.fstat(secret).st_ino}]"
    try:
        result = audit(
            tmp_path,
            directory,
            pack,
            base,
            "--identity",
            str(identity),
            "--passphrase-fd",
            str(secret),
            env={
                "PATH": f"{wrappers}{os.pathsep}{os.environ['PATH']}",
                "PASSPHRASE_PROBE": PASSPHRASE,
            },
            pass_fds=(secret,),
        )
    finally:
        os.close(secret)
    calls = sorted(log.iterdir())
    print(f"sealed audit with the key: verdict {result['verdict']}, {len(calls)} calls logged")
    gate = sealed_gate(result)
    assert (gate["status"], gate["verdict"]) == ("run", "PASS")
    assert any(c.name.endswith(".podman") for c in calls)
    for call in calls:
        lines = call.read_text().splitlines()
        logged = [line for line in lines if not line.startswith("ENV PASSPHRASE_PROBE=")]
        text = "\n".join(logged)
        assert str(keys) not in text, call.name
        assert "identity.age" not in text, call.name
        assert PASSPHRASE not in text, call.name
        assert not any(line.startswith("LEAK ") for line in lines), call.name
        assert not any(line.startswith("FD ") and line.endswith(pipe) for line in lines), call.name
