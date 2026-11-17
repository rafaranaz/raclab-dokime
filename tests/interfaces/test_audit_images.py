# SDD-EARS: INTERFACES-101 INTERFACES-102 INTERFACES-103
from dataclasses import dataclass
from pathlib import Path

from dokime.core.repository import RefusalError
from dokime.core.runtime import Build, BuildLimits
from dokime.core.verdicts import Verdict
from tests.interfaces.audit_runs import BuildsRecorded, ObservesRecorded, audit, base_files, change


def context_of(runtime: BuildsRecorded, image: object) -> dict[str, bytes]:
    (context,) = [
        context
        for position, (_, _, _, context) in enumerate(runtime.builds)
        if runtime.image(position) == image
    ]
    return context


def test_each_side_observes_in_the_image_built_with_its_own_tree() -> None:
    files = base_files(**{"tests/test_p.py": b"base test"})
    observer = ObservesRecorded()
    done = audit(files, change(**{"tests/test_p.py": "patched test"}), observer=observer)
    protected = {gate["gate"]: gate for gate in done.gates()}["protected-paths"]
    assert protected["verdict"] == "FAIL"
    *on_base, on_change = observer.images
    assert len(on_base) == 2
    for image in on_base:
        assert context_of(done.runtime, image)["src/p.py"] == b"code"
    changed = context_of(done.runtime, on_change)
    assert changed["src/p.py"] == b"new"
    assert changed["tests/test_p.py"] == b"base test"
    assert on_change not in on_base


@dataclass
class RefusesTheBuildsOfTheChange(BuildsRecorded):
    def build(self, dockerfile: Path, directory: Path, limits: BuildLimits) -> Build:
        if (directory / "src" / "p.py").read_bytes() == b"new":
            raise RefusalError("build-failed", "the build of the image of the change failed")
        return super().build(dockerfile, directory, limits)


def test_a_refused_build_of_the_change_is_a_finding_of_visible_examples() -> None:
    done = audit(runtime=RefusesTheBuildsOfTheChange())
    visible = {gate["gate"]: gate for gate in done.gates()}["visible-examples"]
    assert [(f["code"], f["verdict"]) for f in visible["findings"]] == [("build-failed", "ERROR")]
    assert done.audited.verdict is Verdict.ERROR


def test_the_image_of_the_change_is_recorded_in_the_ledger() -> None:
    observer = ObservesRecorded()
    done = audit(observer=observer)
    (finished,) = [
        e for e in done.events() if e["type"] == "gate.finished" and e["gate"] == "visible-examples"
    ]
    assert finished["image"] == observer.images[-1].text
