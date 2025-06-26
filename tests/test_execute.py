import pytest
from leanup import __version__
from pathlib import Path

def test_leanup_basic(cache_dir:Path):
    """Test if the package can be imported and cache directory is set."""
    print(f"LeanUp version: {__version__}")
    print(f"LeanUp cache directory: {cache_dir}")
    assert cache_dir is not None, "Cache directory should not be None"