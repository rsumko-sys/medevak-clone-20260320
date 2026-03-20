"""Sync E2E tests — minimal stub."""
import pytest


def test_sync_stats_structure():
    """Sync stats has expected keys (stub — no real sync)."""
    stats = {"pending": 0, "synced": 0, "failed": 0}
    assert "pending" in stats
    assert "synced" in stats
    assert "failed" in stats


def test_sync_queue_is_list():
    """Sync queue is a list (stub)."""
    queue = []
    assert isinstance(queue, list)
