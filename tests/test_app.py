"""End-to-end HTTP tests via FastAPI's TestClient against a temp vault."""

from __future__ import annotations

import importlib

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path, monkeypatch):
    """Build the app against an isolated vault and log in."""
    monkeypatch.setenv("VAULT_DIR", str(tmp_path))
    monkeypatch.setenv("APP_PASSWORD", "test-pass")
    monkeypatch.setenv("APP_SECRET_KEY", "test-secret-key")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    import app.main as main

    importlib.reload(main)
    return TestClient(main.app)


def login(client: TestClient) -> None:
    resp = client.post("/login", data={"password": "test-pass"}, follow_redirects=False)
    assert resp.status_code == 303


def test_requires_login(client):
    resp = client.get("/", follow_redirects=False)
    assert resp.status_code == 303
    assert resp.headers["location"] == "/login"


def test_wrong_password_rejected(client):
    resp = client.post("/login", data={"password": "nope"}, follow_redirects=False)
    assert resp.status_code == 401


def test_dashboard_after_login(client):
    login(client)
    resp = client.get("/")
    assert resp.status_code == 200
    assert "WORK" in resp.text.upper()
    assert "PERSONAL" in resp.text.upper()


def test_command_creates_thread_and_task(client):
    login(client)
    # Create a thread via the heuristic command bar.
    resp = client.post(
        "/command",
        data={"text": "start a new work project called Alpha", "confirm": ""},
    )
    assert resp.status_code == 200
    # Low confidence -> needs confirmation; confirm it.
    resp = client.post(
        "/command",
        data={
            "text": "start a new work project called Alpha",
            "confirm": "create_thread:work:Alpha",
        },
    )
    assert "Created thread work/alpha" in resp.text

    # Add a task through the thread endpoint.
    resp = client.post("/thread/work/alpha/task", data={"title": "Ship it"})
    assert "Ship it" in resp.text

    # Toggle it done.
    resp = client.post("/thread/work/alpha/toggle/0")
    assert "✓" in resp.text


def test_complete_and_restore_flow(client):
    login(client)
    client.post(
        "/command",
        data={
            "text": "start a new personal project called Beta",
            "confirm": "create_thread:personal:Beta",
        },
    )
    resp = client.post("/complete/personal/beta", follow_redirects=False)
    assert resp.status_code == 303
    archive = client.get("/archive")
    assert "Beta" in archive.text
    resp = client.post("/restore/_archive/personal/beta", follow_redirects=False)
    assert resp.status_code == 303
    thread = client.get("/thread/personal/beta")
    assert thread.status_code == 200


def test_health_reports_ai_disabled(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["ai_available"] is False
