"""The line of results that the test of the cases writes for each case it audits (ADR-0081)."""

import json
import subprocess
from pathlib import Path

RESULTS = "DOKIME_CORPUS_RESULTS"
REPOSITORY = Path(__file__).resolve().parents[2]


def result_line(commit: str, key: str, verdict: str, failing: str | None, key_given: bool) -> str:
    """The line of JSON of what the audit of a case gave."""
    fields = {
        "commit": commit,
        "key": key,
        "verdict": verdict,
        "failing_gate": failing,
        "key_given": key_given,
    }
    return json.dumps(fields, separators=(",", ":"))


def append(path: Path, line: str) -> None:
    """Append one line to the file of results."""
    with path.open("a", encoding="utf-8") as results:
        results.write(line + "\n")


def this_commit() -> str:
    """The commit of this repository that the run is made on."""
    done = subprocess.run(
        ["git", "-C", str(REPOSITORY), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    )
    return done.stdout.strip()
