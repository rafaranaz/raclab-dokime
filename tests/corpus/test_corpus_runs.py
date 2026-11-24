# SDD-EARS: CORPUS-099
import hashlib
import io
import json
import subprocess
import tarfile
import tomllib
from pathlib import Path

from dokime.bench.__main__ import report

HERE = Path(__file__).parent
REPOSITORY = HERE.parents[1]


def corpus_at(commit: str, directory: Path) -> Path:
    """`tests/corpus` as it was at a commit, taken out of git into a directory."""
    archive = subprocess.run(
        ["git", "-C", str(REPOSITORY), "archive", commit, "tests/corpus"],
        capture_output=True,
        check=True,
    ).stdout
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
        tar.extractall(directory, filter="data")
    return directory / "tests" / "corpus"


def test_the_metrics_kept_with_a_run_are_those_that_bench_gives_of_its_files(
    tmp_path: Path,
) -> None:
    for run in sorted((HERE / "runs").glob("*/run.toml")):
        recorded = tomllib.loads(run.read_text())
        files = [run.parent / a["file"] for a in recorded["attempt"]]
        for attempt, path in zip(recorded["attempt"], files, strict=True):
            assert hashlib.sha256(path.read_bytes()).hexdigest() == attempt["sha256"], path
        corpus = corpus_at(recorded["commit"], tmp_path / run.parent.name)
        found = report(corpus, files[0], files[1] if len(files) > 1 else None)
        assert found["commit"] == recorded["commit"]
        kept = json.loads((run.parent / "bench.json").read_text())
        assert json.loads(json.dumps(found)) == kept
