"""The command of the runs of R2, for the machine of the maintainer only, with docker.

    DOKIME_CORPUS_IDENTITY=<identity> uv run python -m tests.corpus.contrast.maintainer \\
        OUT RESULTS [--work DIR] [--clones DIR] [--case KEY]...

asks for the passphrase of the identity on the terminal, then runs the arms S0, S1 and S2 of each
case of the corpus that is not withdrawn, or of the cases given, with swarm-verify through
`run_arm.mjs`. Each run is made in a local copy of the base of its case, with the adaptation of its
project and the patch on top, and gives swarm-verify a `SWARM_HOME` of its own, deleted when the
run ends. The evidence of each run stays in `OUT/<project>--<case>/<arm>/`, held-out checks
included, since swarm-verify keeps them in clear; `RESULTS` receives one entry of `runs.py` for each
run, the only thing meant to leave this machine, after review.

This is the one module of the contrast that opens a sealed batch of the corpus (CORPUS-109). The
held-out examples go to the helper of Node only through its input, never to a file written here.
It needs `git`, `uv`, `node` with `npm ci` run in this directory, and docker.
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
import tomllib
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

import yaml

from dokime.contract.check import check
from dokime.contract.model import Example
from dokime.platform.sealed_store import load_identity, read_passphrase
from dokime.verify.sealed import read_batch
from tests.corpus.cases import ACTIVE, Case
from tests.corpus.contrast.convert import files_of
from tests.corpus.contrast.runs import (
    HELD_OUT,
    HELD_OUT_CHECK,
    VISIBLE,
    VISIBLE_CHECK,
    Entry,
    check_command,
    entry_of,
    failed_run,
    in_held_out_conversion,
    toml_of,
    turned_green_by,
)

HERE = Path(__file__).resolve().parent
CORPUS = HERE.parent
HELPER = ("node", str(HERE / "run_arm.mjs"))
ARMS = ("S0", "S1", "S2")
REQUIREMENT = "R1"
IDENTITY = "DOKIME_CORPUS_IDENTITY"
AUTHOR = {
    "GIT_AUTHOR_NAME": "dokime contrast",
    "GIT_AUTHOR_EMAIL": "contrast@dokime.invalid",
    "GIT_COMMITTER_NAME": "dokime contrast",
    "GIT_COMMITTER_EMAIL": "contrast@dokime.invalid",
}

Opener = Callable[[bytes], bytes]
"""What opens a sealed batch: the store of the identity of the maintainer, or of a test."""


@dataclass(frozen=True)
class Spec:
    """What a run needs of a case: where its project is cloned from, its base and patch, the
    adaptation of its project, the contract and the batch of its good case, and its witness."""

    key: str
    origin: str
    base: str
    patch: bytes
    adaptation: Mapping[str, Any]
    contract: str
    sealed: Path | None
    witness: str
    turned_green: tuple[str, ...]
    pack_paths: tuple[str, ...]


def specs(clones: Path | None = None, cases: Sequence[Case] = ACTIVE) -> list[Spec]:
    """The spec of each case, its project cloned from `clones/<project>` or from its address."""
    adaptations = tomllib.loads((HERE / "adaptations.toml").read_text())
    witnesses = tomllib.loads((CORPUS / "witnesses.toml").read_text())["witness"]
    by_case = {f"{w['project']}/{w['case']}": w for w in witnesses if "case" in w}
    found = []
    for case in cases:
        project = CORPUS / case.project
        contract = case.contract
        witness = by_case[f"{case.project}/{contract.parent.name}"]
        pack = yaml.safe_load((project / "pack.yaml").read_text())
        with (project / "source.toml").open("rb") as handle:
            address = tomllib.load(handle)["repository"]
        sealed = contract.parent / "sealed.age"
        found.append(
            Spec(
                key=case.key,
                origin=str(clones / case.project) if clones else address,
                base=str(case.fields["base"]),
                patch=(case.directory / str(case.fields["patch"])).read_bytes(),
                adaptation=adaptations[case.project],
                contract=contract.read_text(),
                sealed=sealed if sealed.exists() else None,
                witness=str(witness["commit"]),
                turned_green=tuple(witness["turned_green"]),
                pack_paths=tuple(pack["tests"]["paths"]),
            )
        )
    return found


def held_out_examples(contract: str, batch: bytes) -> list[Example]:
    """The held-out examples of an opened batch, read with the requirements of the contract; the
    canary is not among them."""
    read = check(contract).contract
    if read is None:
        raise ValueError("the contract cannot be read")
    requirements = "".join(
        "  - " + json.dumps({"id": r.id, "kind": r.kind, "text": r.text, "source": r.source}) + "\n"
        for r in read.requirements
    )
    texts = "".join(example.text for example in read_batch(batch).examples)
    whole = (
        f"format: 1\nstory: {json.dumps(read.story)}\nrequirements:\n{requirements}"
        f"examples:\n{texts}"
    )
    checked = check(whole).contract
    if checked is None:
        raise ValueError("the held-out examples cannot be read")
    return list(checked.examples)


def run_arm(
    spec: Spec,
    arm: str,
    opener: Opener,
    out: Path,
    helper: Sequence[str] = HELPER,
    work: Path | None = None,
) -> Entry:
    """Run one arm on one case and give its entry; a failure of the mount or of the helper is
    recorded by its kind, and the next run goes on. The local copy and the `SWARM_HOME` are made
    in `work`, or in the temporary directory of the system."""
    evidence = out / spec.key.replace("/", "--") / arm
    with (
        tempfile.TemporaryDirectory(prefix="dokime-r2-", dir=work) as copy,
        tempfile.TemporaryDirectory(prefix="dokime-swarm-home-", dir=work) as home,
    ):
        try:
            prepared = _prepare(spec, arm, opener, Path(copy))
        except (subprocess.CalledProcessError, OSError, ValueError, KeyError):
            return failed_run(spec.key, arm, "mount")
        repository, base, candidate, checks, sealed, held_out, requirements = prepared
        request = {
            "repository": str(repository),
            "base": base,
            "candidate": candidate,
            "image": spec.adaptation["image"],
            "out": str(evidence),
            "checks": checks,
            "sealed": sealed,
            "requirements": requirements,
        }
        ended = subprocess.run(
            list(helper),
            input=json.dumps(request),
            capture_output=True,
            text=True,
            env={**os.environ, "SWARM_HOME": home},
            check=False,
        )
        if ended.returncode != 0:
            return failed_run(spec.key, arm, "helper")
        try:
            result = json.loads(ended.stdout)
            observations = json.loads((evidence / "observations.json").read_text())
        except (OSError, ValueError):
            return failed_run(spec.key, arm, "helper")
    return entry_of(spec.key, arm, result, observations, held_out)


def _prepare(
    spec: Spec, arm: str, opener: Opener, work: Path
) -> tuple[
    Path,
    str,
    str,
    list[dict[str, Any]],
    dict[str, Any] | None,
    Callable[[str], bool],
    list[dict[str, Any]],
]:
    """The local copy of a run, its supplied checks, what it seals, which tests are held out and
    the requirement it gives, none in S0."""
    test = str(spec.adaptation["test"])
    read = check(spec.contract).contract
    if read is None:
        raise ValueError("the contract cannot be read")
    laid: dict[str, bytes] = {}
    checks: list[dict[str, Any]] = []
    evidence: list[str] = []
    if arm == "S2":
        visible = files_of({example.id: example for example in read.examples})
        laid = {f"{VISIBLE}/{path}": content for path, content in visible.items()}
        command = check_command(test, [VISIBLE])
        checks = [
            {
                "name": VISIBLE_CHECK,
                "command": command,
                "kind": "test",
                "authority": "user-acceptance",
            }
        ]
        module = VISIBLE.replace("/", ".") + ".test_dokime_examples"
        evidence = [f"{module}::test_dokime_example[{example.id}]" for example in read.examples]
    repository, base, candidate = _mount(spec, work, laid)
    sealed: dict[str, Any] | None = None
    held_out: Callable[[str], bool] = in_held_out_conversion
    if arm == "S1":
        files, moved = _witness_files(spec, repository, base)
        sealed = _sealed(files, test)
        held_out = turned_green_by(spec.turned_green, moved)
    if arm == "S2" and spec.sealed is not None:
        examples = held_out_examples(spec.contract, opener(spec.sealed.read_bytes()))
        named = {f"h{n}": example for n, example in enumerate(examples, start=1)}
        files = {
            f"{HELD_OUT}/{path}": content.decode("utf-8")
            for path, content in files_of(named).items()
        }
        sealed = _sealed(files, check_command(test, [HELD_OUT]))
    requirements = []
    if arm != "S0":
        requirements = [
            {
                "id": REQUIREMENT,
                "text": " ".join(requirement.text for requirement in read.requirements),
                "source": "user",
                "kind": "fix",
                "required": True,
                "evidence": {"tests": [{"name": name} for name in evidence]},
            }
        ]
    return repository, base, candidate, checks, sealed, held_out, requirements


def _sealed(files: Mapping[str, str], command: str) -> dict[str, Any]:
    return {
        "files": [{"path": path, "content": content} for path, content in sorted(files.items())],
        "checks": [
            {
                "name": HELD_OUT_CHECK,
                "command": command,
                "kind": "test",
                "requirements": [REQUIREMENT],
            }
        ],
    }


def _mount(spec: Spec, work: Path, laid: Mapping[str, bytes]) -> tuple[Path, str, str]:
    """A local copy of the base with the adaptation and `laid` committed on it, and the patch of
    the case committed on top: the copy, the commit of the base and that of the candidate."""
    repository = work / "repository"
    _git(work, "clone", "-q", "--no-checkout", spec.origin, str(repository))
    _git(repository, "checkout", "-q", "-B", "contrast", spec.base)
    generate = []
    for name, content in spec.adaptation["files"].items():
        if content.startswith("generate: "):
            generate.append(content.removeprefix("generate: "))
            continue
        _write(repository, name, content.lstrip("\n").encode("utf-8"))
    for command in generate:
        subprocess.run(["bash", "-c", command], cwd=repository, check=True, capture_output=True)
    for name, data in laid.items():
        _write(repository, name, data)
    _git(repository, "add", "-A")
    _git(repository, "commit", "-q", "-m", "the adaptation of the contrast")
    base = _git(repository, "rev-parse", "HEAD")
    subprocess.run(
        ["git", "apply", "--index", "-"],
        cwd=repository,
        input=spec.patch,
        check=True,
        capture_output=True,
    )
    _git(repository, "commit", "-q", "-m", "the patch of the case")
    return repository, base, _git(repository, "rev-parse", "HEAD")


def _witness_files(
    spec: Spec, repository: Path, base: str
) -> tuple[dict[str, str], dict[str, str]]:
    """The files of the tests of the pack that the witness changed, as they are at the witness,
    each at a path that the base does not track, and the paths that were moved to get there."""
    changed = _git(
        repository, "diff", "--name-only", "--no-renames", f"{spec.witness}^", spec.witness
    )
    tracked = set(_git(repository, "ls-tree", "-r", "--name-only", base).splitlines())
    files: dict[str, str] = {}
    moved: dict[str, str] = {}
    for name in changed.splitlines():
        if any(PurePosixPath(name).full_match(glob) for glob in spec.pack_paths):
            path = name
            if name in tracked:
                old = PurePosixPath(name)
                path = str(old.with_name(f"{old.stem}_witness{old.suffix}"))
                moved[name] = path
            if path in tracked:
                raise ValueError("the base tracks the path where the witness file goes")
            files[path] = _git(repository, "show", f"{spec.witness}:{name}", strip=False)
    if not files:
        raise ValueError("the witness changed no file of the tests of the pack")
    return files, moved


def _write(repository: Path, name: str, data: bytes) -> None:
    path = repository / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def _git(directory: Path, *args: str, strip: bool = True) -> str:
    ended = subprocess.run(
        ["git", *args],
        cwd=directory,
        env={**os.environ, **AUTHOR},
        capture_output=True,
        text=True,
        check=True,
    )
    return ended.stdout.strip() if strip else ended.stdout


def main(
    argv: Sequence[str],
    environ: Mapping[str, str] = os.environ,
    passphrase: Callable[[], str] = lambda: read_passphrase(None),
    helper: Sequence[str] = HELPER,
) -> int:
    """Run the arms and append an entry for each run to the file of the results."""
    parser = argparse.ArgumentParser(prog="maintainer")
    parser.add_argument("out", type=Path)
    parser.add_argument("results", type=Path)
    parser.add_argument("--clones", type=Path)
    parser.add_argument("--case", action="append", default=[])
    parser.add_argument("--work", type=Path)
    arguments = parser.parse_args(argv)
    identity = environ.get(IDENTITY, "")
    if not identity or not Path(identity).is_file():
        sys.stderr.write(f"maintainer: {IDENTITY} does not name the file of an identity\n")
        return 2
    store, findings = load_identity(Path(identity), passphrase())
    if findings:
        sys.stderr.write(f"maintainer: {', '.join(f.code for f in findings)}\n")
        return 2
    if arguments.work is not None:
        arguments.work.mkdir(parents=True, exist_ok=True)
    chosen = [case for case in ACTIVE if not arguments.case or case.key in arguments.case]
    for spec in specs(arguments.clones, chosen):
        for arm in ARMS:
            entry = run_arm(spec, arm, store.open, arguments.out, helper, arguments.work)
            with arguments.results.open("a", encoding="utf-8") as results:
                results.write(toml_of(entry))
            print(f"{entry.key} {entry.arm} {entry.state or entry.failure}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
