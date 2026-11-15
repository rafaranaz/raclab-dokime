# SDD-EARS: SANDBOX-065 SANDBOX-066
import pyexpat
from pathlib import Path

import pytest

from dokime.sandbox.podman import PodmanRuntime
from tests.sandbox.engines import refusal
from tests.sandbox.test_podman_opening import fake_podman


def opened(tmp_path: Path) -> PodmanRuntime:
    return PodmanRuntime(podman=str(fake_podman(tmp_path / "bin", "podman version 5.4.2")))


@pytest.mark.parametrize("version", ["expat_2.8.4", "expat_2.7.1", "expat_1.95.8", "nonsense"])
def test_an_expat_older_than_2_8_5_or_unreadable_is_refused_quoting_its_version(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, version: str
) -> None:
    monkeypatch.setattr(pyexpat, "EXPAT_VERSION", version)
    finding = refusal(lambda: opened(tmp_path))
    assert (finding.code, version.removeprefix("expat_") in finding.message) == (
        "expat-too-old",
        True,
    )


@pytest.mark.parametrize("version", ["expat_2.8.5", "expat_2.10.0", "expat_3.0.0"])
def test_an_expat_of_2_8_5_or_later_is_accepted_and_given(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, version: str
) -> None:
    monkeypatch.setattr(pyexpat, "EXPAT_VERSION", version)
    assert opened(tmp_path).expat_version == version.removeprefix("expat_")


def test_the_adapter_gives_the_version_of_the_expat_that_reads_its_reports(tmp_path: Path) -> None:
    assert opened(tmp_path).expat_version == pyexpat.EXPAT_VERSION.removeprefix("expat_")
