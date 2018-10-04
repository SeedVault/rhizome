"""Text fixtures for module authorstool.mongodb."""
import pytest
from dot_repository.mongodb import DotRepository

def test_mongodb_uri_not_found():
    """MongoDB URI not found"""
    with pytest.raises(RuntimeError):
        _ = DotRepository([])
