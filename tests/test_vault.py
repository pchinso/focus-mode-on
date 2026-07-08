"""Tests for the vault engine: parse/write round-trip and repo operations."""

from __future__ import annotations

from datetime import date

import pytest

from app.vault.model import Task, Thread
from app.vault.parser import parse_thread_file
from app.vault.repo import VaultError, VaultRepo
from app.vault.writer import render_thread, write_thread


FIXED = date(2026, 7, 8)


@pytest.fixture
def repo(tmp_path):
    """A fresh VaultRepo with a fixed 'today' for deterministic dates."""
    return VaultRepo(tmp_path, today=lambda: FIXED)


def test_roots_created(repo):
    roots = repo.roots()
    assert [r.rel_path for r in roots] == ["work", "personal"]


def test_render_is_lint_clean_and_orders_done_first():
    thread = Thread(
        title="Demo",
        rel_path="work/demo",
        description="A demo thread.",
        created=FIXED,
        tasks=[
            Task("pending one", done=False),
            Task("finished", done=True, completed=FIXED),
        ],
    )
    text = render_thread(thread)
    # Ends with exactly one newline (MD047).
    assert text.endswith("\n") and not text.endswith("\n\n")
    # Completed task rendered before the pending one.
    assert text.index("- [x] finished") < text.index("- [ ] pending one")
    # Heading surrounded by blank lines.
    assert "\n\n# Demo\n\n" in text


def test_write_then_parse_round_trip(repo, tmp_path):
    thread = Thread(
        title="Round Trip",
        rel_path="work/round-trip",
        description="Body text.",
        created=FIXED,
        tasks=[Task("a", done=True, completed=FIXED), Task("b", done=False)],
    )
    path = write_thread(tmp_path, thread)
    parsed = parse_thread_file(path, "work/round-trip")
    assert parsed.title == "Round Trip"
    assert parsed.description == "Body text."
    titles = [(t.title, t.done) for t in parsed.tasks]
    assert titles == [("a", True), ("b", False)]
    assert parsed.tasks[0].completed == FIXED


def test_create_thread_and_add_task(repo):
    thread = repo.create_thread("work", "New Project")
    assert thread.rel_path == "work/new-project"
    repo.add_task("work/new-project", "First task")
    reloaded = repo.get("work/new-project")
    assert reloaded.pending_count == 1
    assert reloaded.tasks[0].title == "First task"


def test_slug_collision_is_deduped(repo):
    a = repo.create_thread("personal", "Trip")
    b = repo.create_thread("personal", "Trip")
    assert a.rel_path != b.rel_path
    assert b.rel_path == "personal/trip-2"


def test_toggle_task_marks_done_with_date(repo):
    repo.create_thread("work", "Toggle")
    repo.add_task("work/toggle", "do it")
    thread = repo.toggle_task("work/toggle", 0)
    task = thread.sorted_tasks()[0]
    assert task.done is True
    assert task.completed == FIXED
    # Toggling back clears completion.
    thread = repo.toggle_task("work/toggle", 0)
    assert thread.sorted_tasks()[0].done is False
    assert thread.sorted_tasks()[0].completed is None


def test_complete_and_restore_thread(repo, tmp_path):
    repo.create_thread("work", "Archive Me")
    dest = repo.complete_thread("work/archive-me")
    assert dest == "_archive/work/archive-me"
    assert not (tmp_path / "work" / "archive-me").exists()
    archived = repo.archived()
    assert any(t.rel_path == dest for t in _flatten(archived))
    restored = repo.restore_thread(dest)
    assert restored == "work/archive-me"
    assert (tmp_path / "work" / "archive-me").exists()


def test_complete_task_by_title_fuzzy(repo):
    repo.create_thread("work", "Fuzzy")
    repo.add_task("work/fuzzy", "Call the supplier about the quote")
    assert repo.complete_task_by_title("work/fuzzy", "supplier call") is True
    thread = repo.get("work/fuzzy")
    assert thread.sorted_tasks()[0].done is True


def test_path_traversal_rejected(repo):
    with pytest.raises(VaultError):
        repo.get("../etc/passwd")


def _flatten(threads):
    out = []
    for t in threads:
        out.append(t)
        out.extend(_flatten(t.children))
    return out
