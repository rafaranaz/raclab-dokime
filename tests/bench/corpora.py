"""A small corpus written for the tests of bench, and its files of results."""

import json
from pathlib import Path

COMMIT = "a" * 40
CASES = {
    "p/good-one": "good",
    "p/good-two": "good",
    "p/bad-visible": "fails-a-visible-example",
    "p/bad-held": "fails-a-held-out-example",
    "p/bad-gone": "fails-a-visible-example",
    "p/good-gone": "good",
}
WITNESSES = {"p/good-one": "1" * 40, "p/good-two": "2" * 40, "p/good-gone": "3" * 40}


def write_corpus(root: Path, reader_b_two: str = "not-isolated") -> Path:
    for key, label in CASES.items():
        project, name = key.split("/")
        case = root / project / "cases" / name
        case.mkdir(parents=True)
        (case / "case.toml").write_text(f'label = "{label}"\n')
    (root / "pending.toml").write_text("pending = []\n")
    witnesses = "".join(
        f'[[witness]]\nproject = "p"\ncase = "{k.split("/")[1]}"\ncommit = "{c}"\n\n'
        for k, c in WITNESSES.items()
    )
    (root / "witnesses.toml").write_text(witnesses)
    (root / "withdrawn.toml").write_text(
        '[[withdrawn]]\nkey = "p/good-gone"\nreason = "r"\nfirst_run = "x"\nkey_given = false\n'
        'verdict = "FAIL"\nfailing_gate = "protected-paths"\n\n'
        '[[withdrawn]]\nkey = "p/bad-gone"\nreason = "r"\nfirst_run = "x"\nkey_given = false\n'
        'verdict = "PASS"\nfailing_gate = ""\n'
    )
    (root / "held-out-run.toml").write_text(
        '[[run]]\ndate = "d"\n\n[[run.case]]\nkey = "p/bad-held"\nverdict = "FAIL"\n'
        'failing_gate = "sealed-examples"\n'
    )
    blind = root / "blind"
    (blind / "answers").mkdir(parents=True)
    draw = "".join(
        f'[[witness]]\nid = "W0{n}"\nproject = "p"\ncommit = "{c}"\n\n'
        for n, c in ((1, "1" * 40), (2, "2" * 40), (3, "3" * 40))
    )
    (blind / "draw.toml").write_text("seed = 1\n\n" + draw)
    (blind / "answers" / "A-1.txt").write_text(
        "W01 | isolated | - | r\nW02 | isolated | - | r\nW03 | isolated | - | r\n"
    )
    (blind / "answers" / "B-1.txt").write_text(
        f"W01 | isolated | - | r\nW02 | not-isolated | 2 | r\nW02 | {reader_b_two} | - | r\n"
        "W03 | not-isolated | 2 | r\n"
    )
    return root


def write_results(
    path: Path, verdicts: dict[str, str], commit: str = COMMIT, key: bool = False
) -> Path:
    lines = [
        json.dumps(
            {
                "commit": commit,
                "key": k,
                "verdict": v,
                "failing_gate": None if v == "PASS" else "visible-examples",
                "key_given": key,
            }
        )
        for k, v in verdicts.items()
    ]
    path.write_text("\n".join(lines) + "\n")
    return path


RUNNABLE = {
    "p/good-one": "PASS",
    "p/good-two": "FAIL",
    "p/bad-visible": "PASS",
    "p/bad-held": "PASS",
}
