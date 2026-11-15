# SDD-EARS: SANDBOX-050
import pytest

from tests.sandbox.engines import require

MISSING = "dokime-no-such-engine"


def test_a_test_of_a_missing_engine_fails_in_ci(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CI", "true")
    with pytest.raises(pytest.fail.Exception, match=MISSING):
        require(MISSING)


def test_a_test_of_a_missing_engine_skips_outside_ci(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CI", raising=False)
    with pytest.raises(pytest.skip.Exception, match=MISSING):
        require(MISSING)
