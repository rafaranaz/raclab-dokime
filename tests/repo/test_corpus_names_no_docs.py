# SDD-EARS: REPO-174
"""The list of text of ADR-0077 is safe only while no test of the corpus reads a file of `docs/`."""

import re

from tools._common import DEFAULT_ROOT

DOCS = re.compile(r"""["'](?:\./)?docs(?:/|["'])""")


def test_no_test_of_the_corpus_names_a_path_under_docs() -> None:
    named = [
        f"{path.relative_to(DEFAULT_ROOT)}:{number}"
        for path in sorted((DEFAULT_ROOT / "tests" / "corpus").rglob("*.py"))
        for number, line in enumerate(path.read_text().splitlines(), 1)
        if DOCS.search(line)
    ]
    assert named == []


def test_the_check_sees_a_path_under_docs() -> None:
    assert DOCS.search('Path("docs/ROADMAP.md")')
    assert DOCS.search("root / 'docs' / 'adr'")
    assert not DOCS.search('"documents"')
