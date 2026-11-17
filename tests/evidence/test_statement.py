# SDD-EARS: EVIDENCE-001 EVIDENCE-002 EVIDENCE-003 EVIDENCE-004
import hashlib

from dokime.core.canonical import canonical
from dokime.evidence.statement import build
from tests.evidence.runs import run, statement


def test_the_statement_is_an_in_toto_statement_of_the_tree_and_the_patch() -> None:
    given = statement()
    assert given["_type"] == "https://in-toto.io/Statement/v1"
    assert given["predicateType"] == (
        "https://github.com/rafaranaz/raclab-dokime/attestation/conformance/v0.1"
    )
    assert given["subject"] == [
        {"name": "tree", "digest": {"gitTree": "1" * 40}},
        {"name": "change.patch", "digest": {"sha256": hashlib.sha256(b"the patch").hexdigest()}},
    ]
    assert set(given) == {"_type", "subject", "predicateType", "predicate"}


def test_the_bytes_are_the_canonical_form_of_the_statement() -> None:
    built = build(run())
    assert built.data == canonical(statement()).encode("utf-8")
    assert b"\n" not in built.data
    assert build(run()).data == built.data


def test_the_bytes_keep_text_that_is_not_ascii_as_itself() -> None:
    data = build(run(harness="0.0.0-ñ")).data
    assert "0.0.0-ñ".encode() in data


def test_the_digest_is_that_of_the_bytes() -> None:
    built = build(run())
    assert built.digest == "sha256:" + hashlib.sha256(built.data).hexdigest()


def test_the_file_is_named_after_the_story() -> None:
    assert build(run(story="invoice-rounding")).name == "invoice-rounding.statement.json"
