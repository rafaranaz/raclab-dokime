# SDD-EARS: SANDBOX-070 SANDBOX-071
"""A run has no capabilities and cannot gain privileges, as the kernel reports for its process."""

from pathlib import Path

import pytest

from dokime.core.runtime import Ending, RunLimits, VerificationRuntime
from tests.sandbox.engines import BUSYBOX, Engine

STATUS = (
    "grep -E '^(CapInh|CapPrm|CapEff|CapBnd|CapAmb|NoNewPrivs):' /proc/self/status"
    " > /dokime/out/status; touch /tmp/owned;"
    " chown 1:1 /tmp/owned && echo chowned > /dokime/out/chown"
)


@pytest.fixture
def status(engine: Engine, runtime: VerificationRuntime, tmp_path: Path) -> dict[str, str]:
    project, out = tmp_path / "project", tmp_path / "out"
    project.mkdir()
    out.mkdir()
    result = runtime.run(engine.pull(BUSYBOX), ("sh", "-c", STATUS), project, out, RunLimits())
    assert result.ending == Ending.EXITED
    fields = dict(line.split(":\t") for line in (out / "status").read_text().splitlines())
    fields["chown"] = "yes" if (out / "chown").exists() else "no"
    return fields


def test_a_command_has_no_capabilities(status: dict[str, str]) -> None:
    sets = ("CapInh", "CapPrm", "CapEff", "CapBnd", "CapAmb")
    assert {name: status[name] for name in sets} == dict.fromkeys(sets, "0" * 16)


def test_a_command_cannot_do_what_needs_a_capability(status: dict[str, str]) -> None:
    assert status["chown"] == "no"


def test_a_command_cannot_gain_privileges(status: dict[str, str]) -> None:
    assert status["NoNewPrivs"] == "1"
