import tempfile
import pytest
from pathlib import Path
from leanup.const import LEANUP_CACHE_DIR
from leanup.utils import CommandExecutor


@pytest.fixture
def cache_dir():
    """Fixture to provide the LeanUp cache directory."""
    return LEANUP_CACHE_DIR

@pytest.fixture
def executor():
    """Create a CommandExecutor instance for testing"""
    return CommandExecutor()

@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)