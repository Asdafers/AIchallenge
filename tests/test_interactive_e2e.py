"""Integration test for interactive mode - mock Gemini, real endpoints."""

import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient

from methodic.server import create_app


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


def test_interactive_start_returns_stream_url(client):
    with patch("methodic.server._start_interactive_pipeline", new_callable=AsyncMock):
        resp = client.post("/api/interactive/start", json={"preset": "lost_deals"})
    assert resp.status_code == 200
    data = resp.json()
    assert "session_id" in data
    assert "/stream" in data["stream_url"]
    assert data["title"] == "Q1 2026 Lost Deal Analysis"
    assert "VP of Engineering" in data["persona_hint"]


def test_interactive_respond_queues_message(client):
    """Test that POST /respond puts message on the input queue."""
    from methodic.server import _interactive_sessions, _session_lookup, InteractiveSession

    adk_sid = "fake-adk-session"
    session_id = "INT-test1234"
    isess = InteractiveSession(session_id=session_id, adk_session_id=adk_sid)
    isess.input_requested = True  # Must be awaiting input
    _interactive_sessions[adk_sid] = isess
    _session_lookup[session_id] = adk_sid

    try:
        resp = client.post(
            f"/api/interactive/{session_id}/respond",
            json={"message": "It was about price."},
        )
        assert resp.status_code == 200
        assert not isess.input_queue.empty()
    finally:
        _interactive_sessions.pop(adk_sid, None)
        _session_lookup.pop(session_id, None)


def test_interactive_respond_rejects_when_not_awaiting(client):
    """POST /respond should 409 when no input is requested."""
    from methodic.server import _interactive_sessions, _session_lookup, InteractiveSession

    adk_sid = "fake-adk-session-reject"
    session_id = "INT-reject"
    isess = InteractiveSession(session_id=session_id, adk_session_id=adk_sid)
    isess.input_requested = False
    _interactive_sessions[adk_sid] = isess
    _session_lookup[session_id] = adk_sid

    try:
        resp = client.post(
            f"/api/interactive/{session_id}/respond",
            json={"message": "Too early"},
        )
        assert resp.status_code == 409
    finally:
        _interactive_sessions.pop(adk_sid, None)
        _session_lookup.pop(session_id, None)


def test_interactive_status_returns_state(client):
    from methodic.server import _interactive_sessions, _session_lookup, InteractiveSession

    adk_sid = "fake-adk-session-2"
    session_id = "INT-test5678"
    isess = InteractiveSession(session_id=session_id, adk_session_id=adk_sid, status="interviewing")
    isess.input_requested = True
    _interactive_sessions[adk_sid] = isess
    _session_lookup[session_id] = adk_sid

    try:
        resp = client.get(f"/api/interactive/{session_id}/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "interviewing"
        assert data["input_requested"] is True
        assert data["session_id"] == session_id
    finally:
        _interactive_sessions.pop(adk_sid, None)
        _session_lookup.pop(session_id, None)
