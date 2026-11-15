# SDD-EARS: SANDBOX-033
"""An interruption of the harness removes the container of the run and goes on.

The adapter runs in a process of its own, which the test interrupts once its container exists.
"""

import signal
import subprocess
import sys
import time
from pathlib import Path

import pytest

from tests.sandbox.engines import BUSYBOX, Engine

HARNESS = """
import sys
from pathlib import Path
from dokime.core.runtime import Digest, RunLimits
from tests.sandbox.engines import ENGINES

engine = ENGINES[sys.argv[1]]
image, project, out = Digest(sys.argv[2]), Path(sys.argv[3]), Path(sys.argv[4])
engine.adapter().run(image, ("sleep", "120"), project, out, RunLimits())
print("the run returned", flush=True)
"""


@pytest.mark.parametrize("sent", [signal.SIGINT, signal.SIGTERM])
def test_an_interruption_removes_the_container_and_goes_on(
    engine: Engine, tmp_path: Path, sent: signal.Signals
) -> None:
    project, out = tmp_path / "project", tmp_path / "out"
    project.mkdir()
    out.mkdir()
    image = engine.pull(BUSYBOX)
    before = engine.containers()
    harness = subprocess.Popen(
        [sys.executable, "-c", HARNESS, engine.name, image.text, str(project), str(out)],
        cwd=Path(__file__).parents[2],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        deadline = time.monotonic() + 60
        while not engine.containers() - before:
            assert time.monotonic() < deadline, "the container of the run never started"
            assert harness.poll() is None, harness.communicate()
            time.sleep(0.2)
        harness.send_signal(sent)
        stdout, _ = harness.communicate(timeout=60)
    finally:
        harness.kill()
    assert harness.returncode == -sent
    assert "the run returned" not in stdout
    assert engine.containers() <= before
