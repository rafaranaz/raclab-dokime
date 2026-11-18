# SDD-EARS: EVIDENCE-026 EVIDENCE-027 EVIDENCE-028 EVIDENCE-029
from dokime.core.repository import CommitName
from dokime.core.runtime import Digest
from dokime.evidence.run import Image, Repeated
from tests.evidence.runs import PLATFORM, inputs, predicate, run

COMMIT = CommitName("e" * 40)
CHANGE = Digest("sha256:" + "f" * 64)


def test_the_commit_of_the_harness_is_recorded_when_given() -> None:
    assert predicate(run(harness_commit=COMMIT))["verifier"]["commit"] == "e" * 40
    assert "commit" not in predicate()["verifier"]


def test_the_image_of_the_change_is_recorded_when_given() -> None:
    given = predicate(run(inputs=inputs(change_image=Image(CHANGE, PLATFORM))))["inputs"]
    assert given["change_image"] == {"digest": CHANGE.text, "platform": PLATFORM.text}
    alone = predicate(run(inputs=inputs(change_image=Image(CHANGE))))["inputs"]
    assert alone["change_image"] == {"digest": CHANGE.text}
    assert "change_image" not in predicate()["inputs"]


def test_the_repetitions_are_recorded_when_given() -> None:
    assert predicate(run(repeated=Repeated(runs=2, consistent=False)))["repeated"] == {
        "runs": 2,
        "consistent": False,
    }
    assert "repeated" not in predicate()


def test_no_finding_carries_a_trusted_message() -> None:
    findings = [f for gate in predicate()["gates"] for f in gate.get("findings", [])]
    assert findings
    assert all("message" not in finding for finding in findings)
