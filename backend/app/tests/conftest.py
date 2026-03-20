"""Pytest fixtures — minimal stub."""
import pytest


@pytest.fixture
def sample_case():
    """Sample case for tests."""
    return {"id": "test-1", "mechanism_of_injury": "Test", "created_at": "2025-01-01T00:00:00"}
