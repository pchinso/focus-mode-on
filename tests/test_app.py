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


def test_card_pending_panel_lists_tasks_oldest_first(client):
    """v1.1: a card's [+] panel lists pending tasks (oldest first), linkable."""
    login(client)
    approve(client, "create_thread", "work", "Proj")
    client.post("/thread/work/proj/task", data={"title": "Older task"})
    client.post("/thread/work/proj/task", data={"title": "Newer task"})
    page = client.get("/").text
    assert "pending-toggle" in page  # the [+] button
    assert "pending-panel" in page
    assert "Older task" in page and "Newer task" in page
    # Tasks link back to their owning thread.
    assert '/thread/work/proj" class="pending-link"' in page


def test_pending_panel_works_in_both_modes(client):
    """v1.1 bug fix: the card pending panel renders in WORK and PERSONAL."""
    login(client)
    # WORK thread with a pending task.
    approve(client, "create_thread", "work", "WorkProj")
    client.post("/thread/work/workproj/task", data={"title": "Work pending"})
    # PERSONAL thread with a pending task.
    client.post("/mode/personal")
    approve(client, "create_thread", "personal", "Sport")
    client.post("/thread/personal/sport/task", data={"title": "Personal pending"})

    personal = client.get("/").text  # still in personal mode
    assert "pending-toggle" in personal and "Personal pending" in personal

    client.post("/mode/work")
    work = client.get("/").text
    assert "pending-toggle" in work and "Work pending" in work


def test_generated_icon_has_light_chip_css(client):
    """v1.1: img icons get a constant light chip so dark-mode icons stay visible."""
    login(client)
    css = client.get("/static/css/app.css").text
    assert "img.icon" in css and "background: #fff" in css


def test_command_bar_on_every_page(client):
    """v1.1: the AI command box is present on the dashboard AND thread pages."""
    login(client)
    approve(client, "create_thread", "work", "Anywhere")
    dash = client.get("/").text
    thread = client.get("/thread/work/anywhere").text
    assert 'id="command-input"' in dash
    assert 'id="command-input"' in thread  # available while viewing a thread


def test_new_subthread_button_creates_child(client):
    """v1.1: the thread page can create a sub-thread directly."""
    login(client)
    approve(client, "create_thread", "work", "Parent")
    page = client.get("/thread/work/parent").text
    assert "new-thread/work/parent" in page  # the sub-thread form
    resp = client.post(
        "/new-thread/work/parent", data={"title": "Child"}, follow_redirects=False
    )
    assert resp.status_code == 303
    assert resp.headers["location"] == "/thread/work/parent/child"
    assert client.get("/thread/work/parent/child").status_code == 200


def test_move_button_disabled_until_selected(client):
    """v1.1: the Move button starts disabled (needs a destination)."""
    login(client)
    approve(client, "create_thread", "work", "A")
    approve(client, "create_thread", "work", "B")
    page = client.get("/thread/work/b").text
    # The move button renders with a disabled attribute and a hook for JS.
    assert "data-move-btn" in page
    import re as _re
    m = _re.search(r"<button[^>]*data-move-btn[^>]*>", page)
    assert m and "disabled" in m.group(0)


def test_pending_task_shows_age(client):
    """A pending task displays its age based on creation time."""
    login(client)
    approve(client, "create_thread", "work", "Aged")
    client.post("/thread/work/aged/task", data={"title": "Recent"})
    page = client.get("/thread/work/aged").text
    assert 'class="age' in page  # age badge rendered
    assert "ago" in page or "just now" in page


def test_reparent_thread_over_http(client):
    login(client)
    approve(client, "create_thread", "work", "Parent")
    approve(client, "create_thread", "work", "Child")
    # The thread page offers move targets.
    page = client.get("/thread/work/child").text
    assert "move-thread" in page and "Move to" in page
    # Re-parent Child under Parent.
    resp = client.post(
        "/move-thread/work/child",
        data={"new_parent": "work/parent"},
        follow_redirects=False,
    )
    assert resp.status_code == 303
    assert resp.headers["location"] == "/thread/work/parent/child"
    assert client.get("/thread/work/parent/child").status_code == 200


def test_archive_purge_deletes_forever(client):
    login(client)
    approve(client, "create_thread", "work", "Trash")
    client.post("/complete/work/trash")  # archive it
    archive = client.get("/archive").text
    assert "Delete forever" in archive and "data-confirm" in archive
    # Purge it permanently.
    resp = client.post(
        "/purge/_archive/work/trash", follow_redirects=False
    )
    assert resp.status_code == 303
    assert "Trash" not in client.get("/archive").text


def test_archive_delete_all(client):
    login(client)
    approve(client, "create_thread", "work", "One")
    approve(client, "create_thread", "work", "Two")
    client.post("/complete/work/one")
    client.post("/complete/work/two")
    archive = client.get("/archive").text
    assert "Delete all" in archive
    resp = client.post("/purge-all", follow_redirects=False)
    assert resp.status_code == 303
    after = client.get("/archive").text
    assert "One" not in after and "Two" not in after
    assert "Nothing archived yet" in after


def test_archive_shows_undo_toast(client):
    login(client)
    approve(client, "create_thread", "work", "Temp")
    resp = client.post("/complete/work/temp")  # follows redirect to parent
    # The destination page shows an undo toast with a restore action.
    assert "toast" in resp.text
    assert "Undo" in resp.text
    assert "/restore/" in resp.text


def test_edit_before_approve_fields_editable(client):
    login(client)
    resp = client.post("/command", data={"text": "email the accountant"})
    # The queued title/target are editable inputs (not just hidden fields).
    assert 'name="title"' in resp.text and "q-title" in resp.text
    assert 'name="thread_path"' in resp.text and "q-path" in resp.text


def test_reorder_drag_over_http(client):
    """v1.2: drag-and-drop reorder endpoint + draggable rows."""
    login(client)
    approve(client, "create_thread", "work", "Drag")
    for t in ("A", "B", "C"):
        client.post("/thread/work/drag/task", data={"title": t})
    page = client.get("/thread/work/drag").text
    assert 'draggable="true"' in page and 'data-thread="work/drag"' in page
    # Drag C (index 2) before A (index 0).
    resp = client.post("/thread/work/drag/reorder/2", data={"target": "0"})
    assert resp.text.index("C") < resp.text.index("A")


def test_move_and_accent_over_http(client):
    login(client)
    approve(client, "create_thread", "work", "Reorder")
    client.post("/thread/work/reorder/task", data={"title": "A"})
    client.post("/thread/work/reorder/task", data={"title": "B"})
    # Move B (index 1) up above A.
    resp = client.post(
        "/thread/work/reorder/move/1", data={"direction": "up"}
    )
    assert resp.text.index("B") < resp.text.index("A")
    # Set an accent color; the thread page reflects it.
    r = client.post(
        "/accent/work/reorder", data={"color": "#ed696a"}, follow_redirects=False
    )
    assert r.status_code == 303
    page = client.get("/thread/work/reorder").text
    assert "#ed696a" in page  # accent applied to the glyph
    assert "accent-picker" in page


def test_thread_html_report(client):
    """v1.1: a self-contained themed HTML report of a thread."""
    login(client)
    approve(client, "create_thread", "work", "Launch")
    client.post("/thread/work/launch/task", data={"title": "Ship it"})
    resp = client.get("/report/work/launch")
    assert resp.status_code == 200
    body = resp.text
    assert "<!DOCTYPE html>" in body and "<style>" in body  # self-contained
    assert "Launch" in body and "Ship it" in body
    assert "linear-gradient" in body  # Cox identity applied


def test_regen_icon_redirects(client):
    """v1.1: regenerate-icon redirects back (no-op without an API key)."""
    login(client)
    approve(client, "create_thread", "work", "IconThread")
    resp = client.post("/regen-icon/work/iconthread", follow_redirects=False)
    assert resp.status_code == 303
    assert resp.headers["location"] == "/thread/work/iconthread"


def test_rename_and_delete_task_over_http(client):
    login(client)
    approve(client, "create_thread", "work", "EditHttp")
    client.post("/thread/work/edithttp/task", data={"title": "First"})
    # Rename it.
    resp = client.post(
        "/thread/work/edithttp/rename/0", data={"title": "Renamed"}
    )
    assert "Renamed" in resp.text and "First" not in resp.text
    # Delete it.
    resp = client.post("/thread/work/edithttp/delete/0")
    assert "Renamed" not in resp.text
    assert "No tasks yet" in resp.text


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


def test_quick_capture_to_inbox(client):
    """v1.2: quick-capture adds tasks to the active mode's Inbox."""
    login(client)  # WORK mode
    page = client.get("/capture").text
    assert "Quick capture" in page and 'href="/capture"' in page
    # Capture a couple of tasks.
    r = client.post("/capture", data={"text": "Buy stamps"}, follow_redirects=False)
    assert r.status_code == 303
    client.post("/capture", data={"text": "Email Bob"})
    # They land in work/inbox and show on the capture page.
    page = client.get("/capture").text
    assert "Buy stamps" in page and "Email Bob" in page and "Inbox" in page
    assert client.get("/thread/work/inbox").status_code == 200


def test_insights_reports_stats(client):
    """v1.2: the insights page reports per-mode task stats."""
    login(client)
    approve(client, "create_thread", "work", "Proj")
    client.post("/thread/work/proj/task", data={"title": "A"})
    client.post("/thread/work/proj/task", data={"title": "B"})
    client.post("/thread/work/proj/toggle/0")  # complete one
    page = client.get("/insights").text
    assert "Insights" in page and "% complete" in page
    assert "completion-bar" in page
    assert 'href="/insights"' in page


def test_pwa_manifest_and_service_worker(client):
    """v1.2: PWA — manifest is linked/served and the service worker is served."""
    login(client)
    page = client.get("/").text
    assert "manifest.webmanifest" in page and 'name="theme-color"' in page
    man = client.get("/static/manifest.webmanifest")
    assert man.status_code == 200 and "standalone" in man.text
    sw = client.get("/sw.js")
    assert sw.status_code == 200 and "serviceWorker" not in sw.text
    assert "javascript" in sw.headers["content-type"]
    assert sw.headers.get("service-worker-allowed") == "/"


def test_bulk_complete_and_delete(client):
    """v1.2: multi-select bulk complete and delete."""
    login(client)
    approve(client, "create_thread", "work", "Bulk")
    for t in ("One", "Two", "Three"):
        client.post("/thread/work/bulk/task", data={"title": t})
    page = client.get("/thread/work/bulk").text
    assert "task-select" in page and "bulk-toolbar" in page  # selection UI present
    # Bulk-complete the first two (display indices 0 and 1).
    resp = client.post(
        "/thread/work/bulk/bulk/complete", data={"path": ["0", "1"]}
    )
    assert resp.text.count("✓") >= 2  # two marked done
    # Bulk-delete a task (index 0 in the current order).
    before = client.get("/thread/work/bulk").text
    resp = client.post("/thread/work/bulk/bulk/delete", data={"path": ["0"]})
    # One fewer task line than before.
    assert resp.text.count('class="task-row') == before.count('class="task-row') - 1


def test_task_note_over_http(client):
    """v1.2: set and clear a single-line task note."""
    login(client)
    approve(client, "create_thread", "work", "Notes")
    client.post("/thread/work/notes/task", data={"title": "Draft"})
    resp = client.post(
        "/thread/work/notes/note/0", data={"note": "Link: example.com"}
    )
    assert "task-note" in resp.text and "Link: example.com" in resp.text
    # Clear it.
    resp = client.post("/thread/work/notes/note/0", data={"note": ""})
    assert "Link: example.com" not in resp.text


def test_priority_cycle_over_http(client):
    """v1.2: cycling priority shows the high/low marker."""
    login(client)
    approve(client, "create_thread", "work", "Prio")
    client.post("/thread/work/prio/task", data={"title": "Ship"})
    resp = client.post("/thread/work/prio/priority/0")  # normal -> high
    assert "🔺" in resp.text
    resp = client.post("/thread/work/prio/priority/0")  # high -> low
    assert "🔽" in resp.text


def test_due_date_and_agenda(client):
    """v1.2: set a due date and see the task in the right agenda bucket."""
    login(client)
    approve(client, "create_thread", "work", "Ship")
    client.post("/thread/work/ship/task", data={"title": "Release notes"})
    # Set an overdue date.
    resp = client.post("/thread/work/ship/due/0", data={"due": "2020-01-01"})
    assert "📅 2020-01-01" in resp.text and "overdue" in resp.text
    # It appears under Overdue in the agenda.
    agenda = client.get("/agenda").text
    assert "Overdue" in agenda and "Release notes" in agenda
    assert 'href="/agenda"' in agenda  # nav link
    # Clearing the due date removes the badge (the date no longer shows).
    resp = client.post("/thread/work/ship/due/0", data={"due": ""})
    assert "2020-01-01" not in resp.text


def test_search_finds_threads_and_tasks(client):
    """v1.2: full-text search matches thread titles and task text."""
    login(client)
    approve(client, "create_thread", "work", "Migration")
    client.post("/thread/work/migration/task", data={"title": "Call the supplier"})
    # Match a task by its text.
    res = client.get("/search", params={"q": "supplier"}).text
    assert "Call the supplier" in res and "/thread/work/migration" in res
    # Match a thread by its title.
    res = client.get("/search", params={"q": "migrat"}).text
    assert "Migration" in res
    # No match.
    res = client.get("/search", params={"q": "zzznope"}).text
    assert "No threads or tasks match" in res
    # Linked in nav.
    assert 'href="/search"' in res


def test_search_empty_shows_stale_smart_list(client):
    """v1.2: with no query, /search shows the stale-pending smart list."""
    login(client)
    page = client.get("/search").text
    assert "Stale pending tasks" in page


def test_tree_view_shows_hierarchy_both_modes(client):
    """v1.1: /tree renders threads, sub-threads and tasks for both roots."""
    login(client)
    approve(client, "create_thread", "work", "Alpha")
    client.post("/new-thread/work/alpha", data={"title": "Beta"})  # sub-thread
    client.post("/thread/work/alpha/beta/task", data={"title": "Deep task"})
    client.post("/thread/work/alpha/task", data={"title": "Do work thing"})
    client.post("/mode/personal")
    approve(client, "create_thread", "personal", "Health")
    client.post("/thread/personal/health/task", data={"title": "Do personal thing"})

    page = client.get("/tree").text
    assert page.count('data-root="work"') == 1 and page.count('data-root="personal"') == 1
    assert "Alpha" in page and "Health" in page  # both roots
    assert "Beta" in page  # nested sub-thread rendered recursively
    assert "Deep task" in page and "Do work thing" in page  # nested + top task
    assert "Do personal thing" in page  # personal task
    assert "tree-tab" in page and "data-tree-toggle" in page  # tabs + collapse
    # Linked in the header nav.
    assert 'href="/tree"' in page


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
