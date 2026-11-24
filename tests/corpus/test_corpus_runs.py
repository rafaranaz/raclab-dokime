# SDD-EARS: CORPUS-099
import json
import tomllib
from pathlib import Path

from dokime.bench.__main__ import report

HERE = Path(__file__).parent


def test_the_metrics_kept_with_a_run_are_those_that_bench_gives_of_its_files() -> None:
    for run in sorted((HERE / "runs").glob("*/run.toml")):
        recorded = tomllib.loads(run.read_text())
        files = [run.parent / a["file"] for a in recorded["attempt"]]
        found = report(HERE, files[0], files[1] if len(files) > 1 else None)
        assert found["commit"] == recorded["commit"]
        assert json.loads(json.dumps(found)) == json.loads((run.parent / "bench.json").read_text())
