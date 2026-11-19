# SDD-EARS: REPO-160
from pathlib import Path
from typing import Any

import yaml

WORKFLOW = Path(__file__).parents[2] / ".github" / "workflows" / "ci.yml"


def steps() -> list[dict[str, Any]]:
    jobs = yaml.safe_load(WORKFLOW.read_text())["jobs"]
    (job,) = [j for j in jobs.values() if j.get("name") == "lint, types and tests"]
    found: list[dict[str, Any]] = job["steps"]
    return found


def position(name: str) -> int:
    return next(i for i, step in enumerate(steps()) if step.get("name") == name)


def test_the_job_of_the_tests_installs_age_before_the_tests() -> None:
    installs = [
        i
        for i, step in enumerate(steps())
        if "apt-get install" in step.get("run", "") and " age" in step.get("run", "")
    ]
    assert installs
    assert installs[0] < position("Tests and coverage")
