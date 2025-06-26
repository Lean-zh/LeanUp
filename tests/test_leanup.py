#!/usr/bin/env python

"""Tests for `leanup` package."""

import pytest
from leanup.const import LEANUP_CACHE_DIR, OS_TYPE

def test_leanup_basic():
    """Test if the package can be imported."""
    from leanup import __version__
    print(f"LeanUp version: {__version__}")
    print(f"LeanUp cache directory: {LEANUP_CACHE_DIR}")

def test_system():
    """Test if the computer system is recognized."""
    assert OS_TYPE in ['Windows', 'MacOS', 'Linux'], f"Unexpected OS_TYPE: {OS_TYPE}"

