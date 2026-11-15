# SDD-EARS: SANDBOX-010 SANDBOX-011 SANDBOX-012 SANDBOX-013 SANDBOX-014 SANDBOX-015 SANDBOX-016
import platform
import time
from pathlib import Path

import pytest

from dokime.core.runtime import BaseImage, BuildLimits, VerificationRuntime
from tests.sandbox.engines import (
    BUSYBOX,
    BUSYBOX_INDEX,
    BUSYBOX_PLATFORMS,
    ENGINES,
    Engine,
    refusal,
    require,
)


def busybox_platform() -> BaseImage:
    machine = platform.machine()
    if machine not in BUSYBOX_PLATFORMS:
        pytest.skip(f"the digest of busybox for {machine} is not known to the tests")
    return BaseImage(platform=BUSYBOX_PLATFORMS[machine])


def context(tmp_path: Path, dockerfile: str) -> tuple[Path, Path]:
    directory = tmp_path / "context"
    directory.mkdir(parents=True)
    (directory / "Dockerfile").write_text(dockerfile)
    (directory / "marker").write_text("from the context\n")
    return directory / "Dockerfile", directory


def test_the_build_gives_the_digest_of_the_image_it_built(
    tmp_path: Path, engine: Engine, runtime: VerificationRuntime
) -> None:
    engine.pull(BUSYBOX)
    built = runtime.build(
        *context(tmp_path, f"FROM {BUSYBOX}\nCOPY marker /marker\n"), BuildLimits()
    )
    assert engine.read(built.image, "/marker") == "from the context"


def test_the_base_of_a_final_stage_from_an_image_is_the_digest_of_its_platform(
    tmp_path: Path, engine: Engine, runtime: VerificationRuntime
) -> None:
    engine.pull(BUSYBOX)
    dockerfile = f"ARG BASE={BUSYBOX_INDEX}\nFROM docker.io/library/busybox@$BASE\nRUN true\n"
    built = runtime.build(*context(tmp_path, dockerfile), BuildLimits())
    assert built.base == busybox_platform()


def test_the_base_of_a_final_stage_from_an_earlier_stage_is_the_base_of_that_stage(
    tmp_path: Path, engine: Engine, runtime: VerificationRuntime
) -> None:
    dockerfile = f"FROM {BUSYBOX} AS first\nRUN true\nFROM first\nRUN echo second > /second\n"
    engine.pull(BUSYBOX)
    built = runtime.build(*context(tmp_path, dockerfile), BuildLimits())
    assert built.base == busybox_platform()


def test_a_final_stage_from_scratch_has_no_base(
    tmp_path: Path, engine: Engine, runtime: VerificationRuntime
) -> None:
    dockerfile = f"FROM {BUSYBOX} AS tools\nRUN true\nFROM scratch\nCOPY marker /marker\n"
    built = runtime.build(*context(tmp_path, dockerfile), BuildLimits())
    assert built.base is None


def test_every_adapter_gives_the_same_base_for_the_same_dockerfile(tmp_path: Path) -> None:
    bases = set()
    for name, engine in sorted(ENGINES.items()):
        require(engine.name)
        engine.pull(BUSYBOX)
        dockerfile, directory = context(tmp_path / name, f"FROM {BUSYBOX}\nRUN true\n")
        bases.add(engine.adapter().build(dockerfile, directory, BuildLimits()).base)
    assert len(bases) == 1


def test_a_build_that_does_not_end_within_its_time_limit_is_refused_naming_the_limit(
    tmp_path: Path, engine: Engine, runtime: VerificationRuntime
) -> None:
    engine.pull(BUSYBOX)
    before = engine.containers()
    start = time.monotonic()
    try:
        finding = refusal(
            lambda: runtime.build(
                *context(tmp_path, f"FROM {BUSYBOX}\nRUN sleep 120\n"),
                BuildLimits(time_seconds=3),
            )
        )
    finally:
        # A known limit: the stopped build leaves its working container in the store.
        left = engine.containers() - before
        if left:
            engine.command("rm", "--force", *left, check=False)
    assert (finding.code, "3 seconds" in finding.message) == ("build-timed-out", True)
    assert time.monotonic() - start < 60


@pytest.mark.parametrize("step", ["RUN echo the build broke here >&2; exit 3", "COPY missing /"])
def test_a_build_that_fails_is_refused_quoting_its_last_lines(
    tmp_path: Path, engine: Engine, runtime: VerificationRuntime, step: str
) -> None:
    engine.pull(BUSYBOX)
    finding = refusal(
        lambda: runtime.build(*context(tmp_path, f"FROM {BUSYBOX}\n{step}\n"), BuildLimits())
    )
    assert finding.code == "build-failed"
    expected = "the build broke here" if step.startswith("RUN") else "missing"
    assert expected in finding.message
