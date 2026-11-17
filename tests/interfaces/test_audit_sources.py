# SDD-EARS: INTERFACES-093 INTERFACES-094 INTERFACES-095 INTERFACES-096 INTERFACES-097
import hashlib
from dataclasses import dataclass
from pathlib import Path

from dokime.core.repository import RefusalError
from dokime.core.runtime import Build, BuildLimits
from dokime.core.verdicts import Verdict
from tests.interfaces.audit_runs import (
    CONTRACT,
    CONTRACT_PATH,
    DOCKERFILE,
    PACK,
    BuildsRecorded,
    audit,
    base_files,
    change,
)


def sha256(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def test_the_contract_and_the_pack_come_from_the_base_and_never_from_the_patch() -> None:
    rewritten = change(
        **{CONTRACT_PATH: "format: 1\nstory: other\n", ".dokime/pack.yaml": "format: 1\n"}
    )
    done = audit(changed=rewritten)
    predicate = done.statement()["predicate"]
    assert predicate["contract"]["digest"] == sha256(CONTRACT)
    assert predicate["inputs"]["pack"]["digest"] == sha256(PACK)
    protected = {gate["gate"]: gate for gate in done.gates()}["protected-paths"]
    assert protected["verdict"] == "FAIL"


def test_the_gate_contract_has_the_findings_of_the_contract() -> None:
    without = CONTRACT.split(b"\nexamples:")[0] + b"\nexamples: []\n"
    done = audit(base_files(**{CONTRACT_PATH.replace("/", "__"): without}))
    contract = done.gates()[0]
    assert contract["gate"] == "contract"
    assert {f["code"] for f in contract["findings"]} == {"requirement-without-example"}
    assert done.audited.verdict is Verdict.ASK


def test_the_image_is_built_from_the_dockerfile_of_the_base_copied_out_of_the_tree() -> None:
    done = audit()
    dockerfile, data, directory, context = done.runtime.builds[0]
    assert data == DOCKERFILE
    assert {"src/p.py", ".dokime/Dockerfile"} <= context
    assert not dockerfile.is_relative_to(directory)
    environment = done.gates()[1]
    assert (environment["gate"], environment["verdict"]) == ("environment", "PASS")


@dataclass
class RefusesBuilds(BuildsRecorded):
    def build(self, dockerfile: Path, directory: Path, limits: BuildLimits) -> Build:
        raise RefusalError("build-failed", "the build of the image failed")


def test_a_refused_build_is_a_finding_of_the_environment() -> None:
    done = audit(runtime=RefusesBuilds())
    environment = done.gates()[1]
    assert [(f["code"], f["verdict"]) for f in environment["findings"]] == [
        ("build-failed", "ERROR")
    ]
    assert done.audited.verdict is Verdict.ERROR


def test_a_pack_with_a_finding_is_a_finding_of_the_environment() -> None:
    done = audit(base_files(**{".dokime__pack.yaml": b"format: 1\nname: p\n"}))
    environment = done.gates()[1]
    assert environment["findings"]
    assert done.runtime.builds == []


def test_the_gates_of_verify_run_with_the_policy_of_the_base() -> None:
    policy = b"format: 1\nbaseline:\n  runs: 3\nverification:\n  runs: 2\n"
    done = audit(base_files(**{".dokime__policy.yaml": policy}))
    assert len(done.observer.calls) == 3 + 1
    assert len(done.runtime.runs) == 3 + 1
