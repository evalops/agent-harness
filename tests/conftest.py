import pytest

from agent_harness import get_registry


@pytest.fixture(autouse=True)
def clear_global_registry():
    get_registry().clear()
    yield
    get_registry().clear()
