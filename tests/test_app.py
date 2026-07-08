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
    # Do not let a developer's local .env leak into tests.
    monkeypatch.setattr("app.config._load_dotenv", lambda: None)
    import app.main as main

    importlib.reload(main)
    return TestClient(main.app)


def login(client: TestClient) -> None:
    resp = client.post("/login", data={"password": "test-pass"}, follow_redirects=False)
    assert resp.status_code == 303


def test_resolve_parent_avoids_double_nesting():
    """A model-returned full path must not nest a thread inside its own name."""
    import app.main as main

    # Model returned the NEW thread's full path -> strip the duplicated leaf.
    assert main._resolve_parent("work/dev", "dev", "work") == "work"
    # A plain root parent is unchanged.
    assert main._resolve_parent("work", "dev", "work") == "work"
    # Nesting under a genuinely different existing thread is preserved.
    assert main._resolve_parent("work/init", "dev", "work") == "work/init"
    # Empty or non-root parents fall back to the active mode.
    assert main._resolve_parent("", "dev", "personal") == "personal"
    assert main._resolve_parent("dev", "dev", "work") == "work"


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
    # Header mode switch offers both modes...
    assert "WORK" in resp.text.upper()
    assert "PERSONAL" in resp.text.upper()
    # ...and the default active mode is WORK.
    assert "Work mode" in resp.text


def test_mode_switch_persists(client):
    login(client)
    # Default is WORK.
    assert "Work mode" in client.get("/").text
    # Switch to PERSONAL; the redirect lands on the personal dashboard.
    resp = client.post("/mode/personal")
    assert resp.status_code == 200
    assert "Personal mode" in resp.text
    # The cookie persists the choice on a fresh request.
    assert "Personal mode" in client.get("/").text
    # An invalid mode falls back to WORK.
    client.post("/mode/bogus")
    assert "Work mode" in client.get("/").text


def test_command_defaults_thread_to_active_mode(client):
    login(client)
    client.post("/mode/personal")
    # A note that names no root should target the active mode (personal).
    text = "buy groceries this weekend"
    resp = client.post(
        "/command",
        data={"text": text, "confirm": f"create_task:personal:{text}"},
    )
    assert "to personal" in resp.text.lower()


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


def test_nested_subtasks_over_http(client):
    login(client)
    client.post(
        "/command",
        data={
            "text": "start a new work project called Nested",
            "confirm": "create_thread:work:Nested",
        },
    )
    # Add a top-level task.
    client.post("/thread/work/nested/task", data={"title": "Parent"})
    # Add a subtask under it (parent index-path "0").
    resp = client.post(
        "/thread/work/nested/task", data={"title": "Child", "parent": "0"}
    )
    assert "Parent" in resp.text and "Child" in resp.text
    # The rendered tree carries the nested toggle path for the child.
    assert "/toggle/0.0" in resp.text
    # Toggle the nested child done via its dotted path.
    resp = client.post("/thread/work/nested/toggle/0.0")
    assert resp.status_code == 200
    assert "✓" in resp.text

    # The full thread page (which includes the recursive macro) renders.
    page = client.get("/thread/work/nested")
    assert page.status_code == 200
    assert "Parent" in page.text and "Child" in page.text
    assert "data-toggle-collapse" in page.text  # collapse caret present


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
