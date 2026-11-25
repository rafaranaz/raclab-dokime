# SDD-EARS: INTERFACES-190 INTERFACES-191 INTERFACES-192
from pathlib import Path

from dokime.core.findings import Finding
from dokime.core.verdicts import Verdict
from dokime.evidence.run import GateRan
from dokime.evidence.statement import Evidence
from dokime.interfaces.audit import Audited
from dokime.interfaces.audit_command import checked_output
from tests.interfaces.audit_runs import audit
from tests.interfaces.sealed_audits import IMPOSSIBLE, BATCH_BASE, StoreDouble, history
from tests.interfaces.test_audit_sealed import HOLDS, run

EVIDENCE = Evidence(
    name="s.statement.json", data=b'{"verdict": "PASS"}', digest="sha256:" + "d" * 64
)
PASSED = Audited(
    verdict=Verdict.PASS,
    gates=(GateRan("sealed-examples", Verdict.PASS),),
    evidence=EVIDENCE,
    sentinel=IMPOSSIBLE,
)


def output(tmp_path: Path, files: dict[str, bytes | str]) -> Path:
    out = tmp_path / "out"
    out.mkdir(parents=True)
    for name, content in files.items():
        path = out / name
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, str):
            path.symlink_to(content)
        else:
            path.write_bytes(content)
    return out


def sentinel_in_out(audited: Audited) -> Finding:
    assert audited.verdict is Verdict.ERROR
    assert audited.evidence is None
    (found,) = [f for f in audited.findings if f.code == "sentinel-in-out"]
    assert found.verdict is Verdict.ERROR
    assert IMPOSSIBLE not in found.message
    return found


def test_the_run_that_opened_the_batch_gives_its_sentinel() -> None:
    done, _ = run(changed=HOLDS)
    assert done.audited.sentinel == IMPOSSIBLE


def test_a_run_that_did_not_open_the_batch_gives_no_sentinel() -> None:
    done = audit(history=history, ancestors=(BATCH_BASE,), sealed=StoreDouble())
    assert done.audited.sentinel is None


def test_an_output_without_the_sentinel_is_kept_as_it_is(tmp_path: Path) -> None:
    out = output(tmp_path, {"ledger.jsonl": b'{"type": "run.started"}\n'})
    assert checked_output(PASSED, out) == PASSED


def test_the_sentinel_in_the_ledger_ends_in_error_without_evidence(tmp_path: Path) -> None:
    out = output(tmp_path, {"ledger.jsonl": f'{{"leaked": "{IMPOSSIBLE}"}}\n'.encode()})
    found = sentinel_in_out(checked_output(PASSED, out))
    assert "ledger.jsonl" in found.message


def test_the_sentinel_in_the_evidence_ends_in_error_without_evidence(tmp_path: Path) -> None:
    out = output(tmp_path, {"ledger.jsonl": b"{}\n"})
    leaked = Evidence(name="s.statement.json", data=IMPOSSIBLE.encode(), digest=EVIDENCE.digest)
    found = sentinel_in_out(checked_output(Audited(**{**PASSED.__dict__, "evidence": leaked}), out))
    assert "evidence" in found.message


def test_the_sentinel_in_a_path_or_a_link_of_the_output_is_an_error(tmp_path: Path) -> None:
    cases: list[dict[str, bytes | str]] = [
        {f"{IMPOSSIBLE}.txt": b"x"},
        {"link": f"/nowhere/{IMPOSSIBLE}"},
    ]
    for number, files in enumerate(cases):
        sentinel_in_out(checked_output(PASSED, output(tmp_path / str(number), files)))


def test_an_audit_without_a_sentinel_is_not_searched(tmp_path: Path) -> None:
    out = output(tmp_path, {"ledger.jsonl": IMPOSSIBLE.encode()})
    unsealed = Audited(verdict=Verdict.PASS, evidence=EVIDENCE)
    assert checked_output(unsealed, out) == unsealed
