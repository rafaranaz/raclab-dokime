"""The engine and the adapter that each test of the verification runtime runs with."""

import pytest

from dokime.core.runtime import VerificationRuntime
from tests.sandbox.engines import ENGINES, Engine, require


@pytest.fixture(params=sorted(ENGINES))
def engine(request: pytest.FixtureRequest) -> Engine:
    """Each engine with an adapter, so that a test of the port proves every adapter."""
    found = ENGINES[request.param]
    require(found.name)
    return found


@pytest.fixture
def runtime(engine: Engine) -> VerificationRuntime:
    return engine.adapter()
