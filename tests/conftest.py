import pytest
from leanup.const import LEANUP_CACHE_DIR

@pytest.fixture
def cache_dir():
    """Fixture to provide the LeanUp cache directory."""
    return LEANUP_CACHE_DIR
