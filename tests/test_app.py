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
    # A note that names no root is queued against the active mode (personal).
    text = "buy groceries this weekend"
    resp = client.post("/command", data={"text": text})
    assert "Review actions" in resp.text
    # The queued action targets the personal root, and approving confirms it.
    assert 'value="personal"' in resp.text
    applied = approve(client, "create_task", "personal", text)
    assert "to personal" in applied.text.lower()


def approve(client, action, thread_path, title):
    """Approve a single action from the review queue (via /apply)."""
    return client.post(
        "/apply",
        data={"action": [action], "thread_path": [thread_path], "title": [title]},
    )


def test_command_queues_then_applies(client):
    login(client)
    # The command bar only QUEUES actions; nothing is created yet.
    resp = client.post(
        "/command", data={"text": "start a new work project called Alpha"}
    )
    assert resp.status_code == 200
    assert "Review actions" in resp.text
    assert client.get("/thread/work/alpha").status_code == 404  # not applied

    # Approving the action creates it.
    resp = approve(client, "create_thread", "work", "Alpha")
    assert "Created thread work/alpha" in resp.text

    # Add a task through the thread endpoint.
    resp = client.post("/thread/work/alpha/task", data={"title": "Ship it"})
    assert "Ship it" in resp.text

    # Toggle it done.
    resp = client.post("/thread/work/alpha/toggle/0")
    assert "✓" in resp.text


def test_nested_subtasks_over_http(client):
    login(client)
    approve(client, "create_thread", "work", "Nested")
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
    # Personal work happens in PERSONAL mode (AI is scoped to the active mode).
    client.post("/mode/personal")
    approve(client, "create_thread", "personal", "Beta")
    resp = client.post("/complete/personal/beta", follow_redirects=False)
    assert resp.status_code == 303
    archive = client.get("/archive")
    assert "Beta" in archive.text
    resp = client.post("/restore/_archive/personal/beta", follow_redirects=False)
    assert resp.status_code == 303
    thread = client.get("/thread/personal/beta")
    assert thread.status_code == 200


def test_command_queues_actions_without_applying(client):
    """Input is ingested into a review queue; nothing is applied yet."""
    login(client)
    resp = client.post("/command", data={"text": "email the accountant about invoices"})
    assert resp.status_code == 200
    assert "Review actions" in resp.text
    assert "action-tag" in resp.text
    # The queue carries hidden fields for approval, and an Approve button.
    assert 'name="action"' in resp.text
    assert "Approve remaining" in resp.text
    # Each action has its own Discard and OK (approve) controls.
    assert "data-discard" in resp.text
    assert "data-approve" in resp.text


def test_apply_ignores_out_of_mode_action(client):
    """A queued action targeting the other root is not applied."""
    login(client)  # WORK mode
    resp = approve(client, "create_task", "personal/whatever", "x")
    assert "Nothing to apply" in resp.text


def test_command_box_is_multiline_textarea(client):
    """The command input is a 10-row textarea, not a single-line field."""
    login(client)
    page = client.get("/").text
    assert "<textarea" in page and 'rows="10"' in page and 'id="command-input"' in page
    # The digestion step only interprets; the loading text must not claim icons.
    assert "generating any new icon" not in page
    assert "Thinking" in page


def test_command_box_keyboard_reachable_with_tips_and_examples(client):
    """The box is autofocused; tips and an Examples help button are present."""
    login(client)
    page = client.get("/").text
    assert "autofocus" in page  # reachable on entry (feat 7)
    assert 'id="command-tips"' in page and 'class="tip"' in page  # tips (feat 8)
    assert 'data-template="new thread NAME"' in page  # a usable template
    assert 'id="examples-toggle"' in page  # examples help button (feat 9)


def test_work_mode_ignores_personal_input(client):
    """In WORK mode, a note aimed at PERSONAL is not queued — it's ignored."""
    login(client)  # default mode is WORK
    resp = client.post("/command", data={"text": "personal buy milk"})
    assert resp.status_code == 200
    assert "Ignored" in resp.text and "WORK" in resp.text
    # And no personal thread was touched.
    assert client.get("/thread/personal/personal").status_code == 404


def test_work_mode_forces_new_thread_into_work(client):
    """Approving a 'personal' create_thread in WORK mode lands it under work/."""
    login(client)
    resp = approve(client, "create_thread", "personal", "Zeta")
    assert "Created thread work/zeta" in resp.text


def test_create_thread_schedules_icon_in_background(tmp_path, monkeypatch):
    """Approving a create_thread defers icon generation to a background task."""
    monkeypatch.setenv("VAULT_DIR", str(tmp_path))
    monkeypatch.setenv("APP_PASSWORD", "p")
    monkeypatch.setenv("APP_SECRET_KEY", "k")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr("app.config._load_dotenv", lambda: None)
    import importlib

    import app.main as main

    importlib.reload(main)
    from fastapi import BackgroundTasks

    from app.ai.commands import Intent

    bg = BackgroundTasks()
    line = main._apply_intent(Intent("create_thread", "work", "BgTest"), "work", bg=bg)
    assert "Created thread work/bgtest" in line
    # The (slow) icon call is queued as a background task, not run inline.
    assert len(bg.tasks) == 1


def test_intent_in_mode_helper():
    import app.main as main
    from app.ai.commands import Intent

    assert main._intent_in_mode(Intent("create_task", "work/x", "t"), "work") is True
    assert main._intent_in_mode(Intent("create_task", "personal/x", "t"), "work") is False
    # create_thread is always allowed (its parent is forced into the mode).
    assert main._intent_in_mode(Intent("create_thread", "personal", "t"), "work") is True


def test_dashboard_has_search_and_palette(client):
    """v1.1: dashboard search box, command palette, and Ctrl+K wiring exist."""
    login(client)
    approve(client, "create_thread", "work", "Alpha")  # ensure a card is present
    page = client.get("/").text
    assert 'id="dashboard-search"' in page  # search/filter box
    assert 'id="palette-overlay"' in page and 'id="palette-input"' in page


def test_threads_json_lists_active_threads(client):
    """v1.1: /threads.json powers the command palette."""
    login(client)
    approve(client, "create_thread", "work", "Reporting")
    client.post("/mode/personal")
    approve(client, "create_thread", "personal", "Health")
    data = client.get("/threads.json").json()
    paths = {t["path"] for t in data["threads"]}
    assert "work/reporting" in paths and "personal/health" in paths
    # Root nodes themselves are not listed as jump targets.
    assert "work" not in paths and "personal" not in paths


def test_review_queue_has_discard_all(client):
    """v1.1: the review queue offers a Discard all control."""
    login(client)
    resp = client.post("/command", data={"text": "email the accountant"})
    assert "data-discard-all" in resp.text


def test_app_has_logo_and_favicon(client):
    """The header shows a vector logo mark and the favicon is served."""
    login(client)
    page = client.get("/").text
    assert "brand-logo" in page  # inline SVG logo in the header
    assert "favicon.svg" in page  # tab icon linked
    fav = client.get("/static/favicon.svg")
    assert fav.status_code == 200
    assert "svg" in fav.headers["content-type"]


def test_health_reports_ai_disabled(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["ai_available"] is False
