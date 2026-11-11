# SDD-EARS: PACKS-001 PACKS-002 PACKS-003 PACKS-004 PACKS-005
from dokime.core.verdicts import Verdict
from dokime.packs.check import check
from dokime.packs.model import Pack
from tests.packs.packs import VALID, codes, seeded


def test_a_valid_pack_has_no_finding_and_is_returned() -> None:
    checked = check(VALID)
    assert checked.findings == ()
    assert checked.verdict is Verdict.PASS
    assert checked.pack == Pack(
        name="cachetools",
        dockerfile="Dockerfile",
        command=("python", "-m", "pytest", "--junitxml", "/dokime/out/report.xml"),
        report="report.xml",
        test_paths=("tests/**", "src/**/test_*.py"),
    )


def test_the_findings_of_the_reader_are_reported_with_those_of_the_pack() -> None:
    checked = seeded("name: cachetools", "name: cachetools\nname: other\nowner: me")
    assert codes(checked) == ["duplicate-key", "unknown-field"]
    assert {finding.verdict for finding in checked.findings} == {Verdict.FAIL}


def test_a_text_the_reader_gives_no_value_for_has_only_the_findings_of_the_reader() -> None:
    checked = check("format: 1\nname: &n x\ntests: *n\n")
    assert codes(checked) == ["anchor-or-alias", "anchor-or-alias"]
    assert checked.pack is None


def test_every_finding_is_reported_at_once_in_the_order_of_the_lines() -> None:
    text = VALID.replace("format: 1", "format: 2").replace("report: report.xml", "report: 3")
    assert [(f.code, f.lines) for f in check(text).findings] == [
        ("unknown-value", (1,)),
        ("wrong-type", (7,)),
    ]


def test_a_pack_with_a_finding_is_not_returned() -> None:
    assert seeded("format: 1", "format: 2").pack is None
