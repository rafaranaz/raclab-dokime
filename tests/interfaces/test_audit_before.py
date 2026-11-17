# SDD-EARS: INTERFACES-110 INTERFACES-111 INTERFACES-112
from dataclasses import dataclass
from pathlib import Path

import pytest

from dokime.core.repository import RefusalError, TreeName
from dokime.core.verdicts import Verdict
from tests.interfaces.audit_runs import CONTRACT, audit, base_files
from tests.verify.doubles import AuditedDouble, patch


def test_a_patch_that_does_not_apply_ends_before_the_run() -> None:
    done = audit(changed=patch(removes=["absent.py"]))
    assert done.audited.verdict is Verdict.ERROR
    assert [f.code for f in done.audited.findings] == ["patch-does-not-apply"]
    assert (done.audited.evidence, done.store.lines()) == (None, ())


@dataclass
class RefusesExtract(AuditedDouble):
    def extract(self, tree: TreeName, directory: Path) -> None:
        raise RefusalError("extract-failed", "the tree cannot be extracted")


def test_a_base_that_cannot_be_extracted_ends_before_the_run() -> None:
    done = audit(repository=RefusesExtract())
    assert [f.code for f in done.audited.findings] == ["extract-failed"]
    assert (done.audited.evidence, done.store.lines()) == (None, ())


def test_a_policy_with_a_finding_ends_before_the_run() -> None:
    done = audit(base_files(**{".dokime__policy.yaml": b"format: 1\nextra: 1\n"}))
    assert done.audited.verdict is Verdict.ERROR
    assert done.audited.findings
    assert (done.audited.evidence, done.store.lines()) == (None, ())


@pytest.mark.parametrize("story", ["a/b", "1-story", ""])
def test_a_story_that_is_not_a_name_ends_before_the_run(story: str) -> None:
    done = audit(story=story)
    assert [(f.code, f.verdict) for f in done.audited.findings] == [("not-a-story", Verdict.ERROR)]
    assert (done.audited.evidence, done.store.lines()) == (None, ())


def test_the_directory_of_a_contract_from_outside_has_to_be_a_name(tmp_path: Path) -> None:
    outside = tmp_path / "not a name" / "contract.yaml"
    outside.parent.mkdir()
    outside.write_bytes(CONTRACT)
    done = audit(story=None, contract=outside)
    assert [f.code for f in done.audited.findings] == ["not-a-story"]
