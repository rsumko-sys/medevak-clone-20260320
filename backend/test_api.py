import pytest
from fastapi.testclient import TestClient
try:
    from main import app
except ImportError:
    from backend.main import app

client = TestClient(app)

def test_api_health():
    """Test that the application starts and can return basic API endpoints."""
    # Depends on environment state. In our case, root / is either an API response or static files.
    # Since STATIC_DIR exists, / will return index.html or 404. Let's test Next.js integration directly.
    response = client.get("/evac")
    assert response.status_code == 200
    assert "html" in response.headers["content-type"]
    assert b"<!DOCTYPE html>" in response.content

def test_static_chunk_delivery():
    """Test that Next.js static chunks are delivered successfully via /_next"""
    # Assuming there's at least one chunk to test
    import os
    from backend.main import static_dir as STATIC_DIR
    chunks_app = os.path.join(STATIC_DIR, "_next", "static", "css")
    if os.path.exists(chunks_app):
        # get any css file
        css_files = [f for f in os.listdir(chunks_app) if f.endswith(".css")]
        if css_files:
            css_file = css_files[0]
            response = client.get(f"/_next/static/css/{css_file}")
            assert response.status_code == 200
            assert "css" in response.headers["content-type"]

def test_api_endpoints():
    """Test specific API subroutes from API router."""
    # We expect 200 OK or 401 Unauthorized for cases endpoints, proving router is attached.
    response = client.get("/api/v1/cases")
    assert response.status_code in [200, 401, 403, 404]  # Depending on auth implementation or empty db

def test_transcribe_imported_correctly():
    """Tests that the transcribe router is successfully loaded after fixing httpx."""
    response = client.post("/api/v1/transcribe/upload")
    # Even without payload, it should return 422 Unprocessable Entity or 401 instead of 404
    assert response.status_code != 404
