"""Tests for interactive mode API endpoints."""

import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient

from methodic.server import create_app


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


def test_interactive_start_with_preset(client):
    with patch("methodic.server._start_interactive_pipeline", new_callable=AsyncMock):
        response = client.post(
            "/api/interactive/start",
            json={"preset": "lost_deals"},
        )
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert "stream_url" in data
    assert data["stream_url"].startswith("/api/interactive/")


def test_interactive_start_with_custom(client):
    with patch("methodic.server._start_interactive_pipeline", new_callable=AsyncMock):
        response = client.post(
            "/api/interactive/start",
            json={"topic": "Custom study", "persona": "Custom persona"},
        )
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data


def test_interactive_start_invalid(client):
    response = client.post(
        "/api/interactive/start",
        json={},
    )
    assert response.status_code == 400


def test_interactive_respond_unknown_session(client):
    response = client.post(
        "/api/interactive/unknown-id/respond",
        json={"message": "Hello"},
    )
    assert response.status_code == 404


def test_interactive_respond_empty_message(client):
    response = client.post(
        "/api/interactive/unknown-id/respond",
        json={"message": ""},
    )
    assert response.status_code == 400


def test_interactive_status_unknown_session(client):
    response = client.get("/api/interactive/unknown-id/status")
    assert response.status_code == 404


def test_interactive_results_unknown_session(client):
    response = client.get("/api/interactive/unknown-id/results")
    assert response.status_code == 404
